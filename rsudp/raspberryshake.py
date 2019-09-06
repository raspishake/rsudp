import sys, os
import socket as s
import signal
from threading import Thread
from queue import Queue
from obspy import read_inventory
from obspy.core.trace import Trace
from obspy.core.stream import Stream
from obspy.signal.trigger import recursive_sta_lta
import numpy as np
from obspy import UTCDateTime
from datetime import datetime, timedelta
import time
import matplotlib
try:
	matplotlib.use('Qt5Agg')
except:
	matplotlib.use('TkAgg')

###########
#Profiling#
import cProfile, pstats, io
from pstats import SortKey
###########

qsize = 120 			# max UDP queue size is 30 seconds' worth of seismic data
queue = Queue(qsize)	# master queue
destinations = []		# queues to write to

initd, sockopen, active = False, False, False
to = 10					# socket test timeout
firstaddr = ''			# the first address data is received from
inv = False				# station inventory
producer, consumer = False, False # state of producer and consumer threads
stn = 'Z0000'			# station name
net = 'AM'				# network (this will always be AM)
chns = []				# list of channels
numchns = 0


tf = None				# transmission frequency in ms
sps = None				# samples per second


def printM(msg, sender=''):
	'''Prints messages with datetime stamp.'''
	msg = '[%s] %s' % (sender, msg) if sender != '' else msg
	print('%s %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg))

sock = s.socket(s.AF_INET, s.SOCK_DGRAM | s.SO_REUSEADDR)

def handler(signum, frame):
	'''The signal handler for the nodata alarm.'''
	printM('No data received in %s seconds; aborting.' % (to))
	printM('Check that no other program is using the port, and that the Shake')
	printM('is forwarding data to the port correctly.')
	raise IOError('No data received')

def initRSlib(dport=8888, rsstn='Z0000', timeout=10):
	'''
	Set values for data port, station, network, and data port timeout prior to opening the socket.
	Defaults:
	dport=8888		# this is the port number to be opened
	rsstn='Z0000'	# the name of the station (something like R0E05)
	timeout=10		# the number of seconds to wait for data before an error is raised (zero for unlimited wait)
	'''
	global port, stn, net, to, initd
	global producer, consumer
	producer, consumer = False, False
	net = 'AM'
	initd = False				# initialization has not completed yet, therefore false
	try:						# set port value first
		if dport == int(dport):
			port = int(dport)
		else:
			port = int(dport)
			printM('WARNING: Supplied port value was converted to integer. Non-integer port numbers are invalid.')
	except ValueError as e:
		printM('ERROR: You likely supplied a non-integer as the port value. Your value: %s'
				% dport)
		printM('Error details: %s' % e)
	except Exception as e:
		printM('ERROR. Details: ' + e)

	try:						# set station name
		if len(rsstn) == 5:
			stn = str(rsstn).upper()
		else:
			stn = str(rsstn).upper()
			printM('WARNING: Station name does not follow Raspberry Shake naming convention. Ignoring.')
	except ValueError as e:
		printM('ERROR: Invalid station name supplied.')
		printM('Error details: %s' % e)
	except Exception as e:
		printM('ERROR. Details:' % e)
	
	try:						# set timeout value 
		to = int(timeout)
	except ValueError as e:
		printM('ERROR: You likely supplied a non-integer as the timeout value. Your value was: %s'
				% timeout)
		printM('       Continuing with default timeout of %s sec'
				% (to))
		printM('Error details: %s' % e)
	except Exception as e:
		printM('ERROR. Details: ' + e)

	initd = True				# if initialization goes correctly, set initd to true

def openSOCK(host=''):
	'''Initialize a socket at a port. Must be done after the above function is called.'''
	global sockopen
	sockopen = False
	if initd:
		HP = '%s:%s' % ('localhost',port)
		printM("Opening socket on %s (HOST:PORT)"
				% HP, 'openSOCK')
		sock.bind((host, port))
		sockopen = True
	else:
		raise IOError("Before opening a socket, you must initialize this raspberryshake library by calling initRSlib(dport=XXXXX, rssta='R0E05') first.")

def test_connection():
	global to
	signal.signal(signal.SIGALRM, handler)
	signal.alarm(to)			# alarm time set with timeout value
	data = sock.recv(4096)
	signal.alarm(0)				# once data has been received, turn alarm completely off
	to = 0						# otherwise it erroneously triggers after keyboardinterrupt
	getTR(getCHNS()[0])
	getSR(tf, data)
	getTTLCHN()

def getDATA():
	'''Read a data packet off the port.
	Alarm if no data is received within timeout.'''
	global to, firstaddr
	if sockopen:
		signal.signal(signal.SIGALRM, handler)
		signal.alarm(to)		# alarm time set with timeout value
		data = sock.recv(4096)
		signal.alarm(0)			# once data has been received, turn alarm completely off
		to = 0					# otherwise it erroneously triggers after keyboardinterrupt
		return data
	else:
		if initd:
			raise IOError("No socket is open. Please open a socket using this library's openSOCK() function.")
		else:
			raise IOError('No socket is open. Please initialize the library then open a socket using openSOCK().')
	
def getCHN(DP):
	'''Extract the channel information from the data packet.
	Requires getDATA() packet as argument.'''
	return str(DP.decode('utf-8').split(",")[0][1:]).strip("\'")
	
def getTIME(DP):
	'''Extract the timestamp from the data packet.
	Timestamp is seconds since 1970-01-01 00:00:00Z,
	which can be passed directly to an obspy UTCDateTime object.
	Requires getDATA() packet as argument.'''
	return float(DP.split(b",")[1])

def getSTREAM(DP):
	'''Get the samples in a data packet as a list object.
	Requires getDATA() packet as argument.'''
	return list(map(int, DP.decode('utf-8').replace('}','').split(',')[2:]))

def getTR(chn):				# DP transmission rate in msecs
	'''Get the transmission rate in milliseconds.
	Requires a getCHN() or a channel name string as argument.'''
	global tf
	timeP1, timeP2 = 0.0, 0.0
	done = False
	while not done:
		DP = getDATA()
		CHAN = getCHN(DP)
		if CHAN == chn:
			if timeP1 == 0.0:
				timeP1 = getTIME(DP)
			else:
				timeP2 = getTIME(DP)
				done = True
	TR = timeP2*1000 - timeP1*1000
	tf = int(TR)
	return tf

def getSR(TR, DP):
	'''Get the sample rate in samples per second.
	Requires an integer transmission rate and a data packet as arguments.'''
	global sps
	sps = int((DP.count(b",") - 1) * 1000 / TR)
	return sps
	
def getCHNS():
	'''Get a list of channels sent to the port.	'''
	global chns
	chdict = {'EHZ': False, 'EHN': False, 'EHE': False,
			  'ENZ': False, 'ENN': False, 'ENE': False, 'HDF': False}
	firstCHN = ''
	done = False
	sim = 0
	while not done:
		DP = getDATA()
		if firstCHN == '':
			firstCHN = getCHN(DP)
			chns.append(firstCHN)
			continue
		nextCHN = getCHN(DP)
		if firstCHN == nextCHN:
			if sim > 1:
				done = True
				continue
			sim += 1
		else:
			chns.append(nextCHN)
	for ch in chns:
		chdict[ch] = True
	chns = []
	for ch in chdict:
		if chdict[ch] == True:
			chns.append(ch)
	return chns

def getTTLCHN():
	'''Calculate total number of channels received.'''
	global numchns
	numchns = len(getCHNS())
	return numchns


def get_inventory(stn='Z0000', sender='get_inventory'):
	global inv
	sender = 'get_inventory'
	if 'Z0000' in stn:
		printM('No station name given, continuing without inventory.',
				sender)
		inv = False
	else:
		try:
			printM('Fetching inventory for station %s.%s from Raspberry Shake FDSN.'
					% (net, stn), sender)
			inv = read_inventory('https://fdsnws.raspberryshakedata.com/fdsnws/station/1/query?network=%s&station=%s&level=resp&format=xml'
								 % (net, stn))
			printM('Inventory fetch successful.', sender)
		except IndexError:
			printM('Inventory fetch failed, continuing without.',
					sender)
			inv = False
	return inv


def make_trace(d):
	'''Makes a trace and assigns it some values using a data packet.'''
	ch = getCHN(d)						# channel
	if ch:# in channels:
		t = getTIME(d)				# unix epoch time since 1970-01-01 00:00:00Z; "timestamp" in obspy
		st = getSTREAM(d)				# samples in data packet in list [] format
		tr = Trace(data=np.ma.MaskedArray(st, dtype=np.int32))	# create empty trace
		tr.stats.network = net			# assign values
		tr.stats.location = '00'
		tr.stats.station = stn
		tr.stats.channel = ch
		tr.stats.sampling_rate = sps
		tr.stats.starttime = UTCDateTime(t)
		if inv:
			try:
				tr.attach_response(inv)
			except:
				printM('ERROR attaching inventory response. Are you sure you set the station name correctly?')
				printM('    This could indicate a mismatch in the number of data channels between the inventory and the stream.')
				printM('    For example, if you are receiving RS4D data, please make sure the inventory you download has 4 channels.')
		return tr

# Then make repeated calls to this, to continue adding trace data to the stream
def update_stream(stream, d, **kwargs):
	'''Returns an updated trace object with new data, merged down to one trace per available channel.'''
	while True:
		try:
			return stream.append(make_trace(d)).merge(**kwargs)
		except TypeError:
			pass


class ProducerThread(Thread):
	def __init__(self, port, stn='Z0000'):
		"""
		Initialize the thread
		"""
		self.sender = 'ProducerThread'
		self.active = False

		if not self.active:
			super().__init__()
			printM('Starting.', self.sender)
			initRSlib(dport=port, rsstn=stn)
			openSOCK()
			printM('Waiting for UDP data on port %s...' % (port), self.sender)
			test_connection()
			self.active = True
		else:
			printM('Error: Producer thread already started', self.sender)

	def run(self):
		"""
		Receives data from one IP address and puts it in an async queue.
		Prints each sending address to STDOUT so the user can troubleshoot.
		This will work best on local networks where a router does not obscure
		multiple devices behind one sending IP.
		Remember, RS UDP packets cannot be differentiated by sending instrument.
		Their identifiers are per channel (EHZ, HDF, ENE, SHZ, etc.)
		and not per Shake (R4989, R52CD, R24FA, RCB43, etc.). To avoid problems,
		please use a separate port for each Shake.
		"""
		global to
		global queue
		firstaddr = ''
		blocked = []
		while True:
			data, addr = sock.recvfrom(4096)
			if firstaddr == '':
				firstaddr = addr[0]
				printM('Receiving UDP data from %s' % (firstaddr), self.sender)
			if (firstaddr != '') and (addr[0] == firstaddr):
				queue.put(data)
			else:
				if addr[0] not in blocked:
					printM('Another IP (%s) is sending UDP data to this port. Ignoring...'
							% (addr[0]), self.sender)
					blocked.append(addr[0])


class ConsumerThread(Thread):
	def __init__(self):
		"""
		Initialize the thread
		"""
		global destinations
		destinations = []
		self.active = False
		self.sender = 'ConsumerThread'

		if not self.active:
			super().__init__()
			self.active = True
			printM('Starting.', self.sender)
		else:
			printM('Error: Consumer thread already started', self.sender)

	def run(self):
		"""
		Distributes queue objects to execute various other tasks: for example,
		it may be used to populate ObsPy streams for various things like
		plotting, alert triggers, and ground motion calculation.
		"""
		global queue

		while True:
			p = queue.get()
			queue.task_done()

			for q in destinations:
				q.put(p)


class PrintThread(Thread):
	def __init__(self):
		"""
		Initialize the thread
		"""
		super().__init__()
		global destinations

		prntq = Queue(qsize)
		destinations.append(prntq)
		self.qno = len(destinations) - 1
		self.sender = 'PrintThread'
		printM('Starting.', self.sender)

	def run(self):
		"""

		"""

		while True:
			d = destinations[self.qno].get()
			destinations[self.qno].task_done()
			print(str(d))


class AlertThread(Thread):
	def __init__(self, sta=5, lta=30, thresh=1.6, bp=False, func='print',
				 debug=True, cha='HZ', *args, **kwargs):
		
		"""
		A recursive STA-LTA 
		:param float sta: short term average (STA) duration in seconds
		:param float lta: long term average (LTA) duration in seconds
		:param float thresh: threshold for STA/LTA trigger
		:type bp: :py:class:`bool` or :py:class:`list`
		:param bp: bandpass filter parameters
		:param func func: threshold for STA/LTA trigger
		:param bool debug: threshold for STA/LTA trigger
		:param str cha: listening channel (defaults to [S,E]HZ)
		"""
		super().__init__()
		global destinations
		self.default_ch = 'HZ'
		self.sta = sta
		self.lta = lta
		self.thresh = thresh
		self.func = func
		self.debug = debug
		self.args = args
		self.kwargs = kwargs
		self.stream = Stream()
		cha = self.default_ch if (cha == 'all') else cha
		self.cha = cha if isinstance(cha, str) else cha[0]
		self.sps = sps
		self.sender = 'AlertThread'
		if bp:
			self.freqmin = bp[0]
			self.freqmax = bp[1]
			if (bp[0] <= 0) and (bp[1] >= (sps/2)):
				self.filt = False
			elif (bp[0] > 0) and (bp[1] >= (sps/2)):
				self.filt = 'highpass'
				self.freq = bp[0]
			elif (bp[0] <= 0) and (bp[1] <= (sps/2)):
				self.filt = 'lowpass'
				self.freq = bp[1]
			else:
				self.filt = 'bandpass'
		else:
			self.filt = False

		alrtq = Queue(qsize)
		destinations.append(alrtq)
		self.qno = len(destinations) - 1

		listen_ch = '?%s' % self.default_ch if self.cha == self.default_ch else self.cha
		printM('Starting Alert trigger with sta=%ss, lta=%ss, and threshold=%s on channel=%s'
				% (self.sta, self.lta, self.thresh, listen_ch), self.sender)
		if self.filt == 'bandpass':
			printM('Alert stream will be %s filtered from %s to %s Hz'
					% (self.filt, self.freqmin, self.freqmax), self.sender)
		elif self.filt in ('lowpass', 'highpass'):
			modifier = 'below' if self.filt in 'lowpass' else 'above'
			printM('Alert stream will be %s filtered %s %s Hz'
					% (self.filt, modifier, self.freq), self.sender)

	def getq(self):
		d = destinations[self.qno].get()
		destinations[self.qno].task_done()
		if self.cha in str(d):
			self.stream = update_stream(
				stream=self.stream, d=d, fill_value='latest')
			return True
		else:
			return False
	
	def set_sps(self):
		self.sps = self.stream[0].stats.sampling_rate

	def copy(self):
		stream = Stream()
		for t in range(len(self.stream)):
			trace = Trace(data=self.stream[t].data)
			trace.stats.network = self.stream[t].stats.network
			trace.stats.location = self.stream[t].stats.location
			trace.stats.station = self.stream[t].stats.station
			trace.stats.channel = self.stream[t].stats.channel
			trace.stats.sampling_rate = self.stream[t].stats.sampling_rate
			trace.stats.starttime = self.stream[t].stats.starttime
			stream.append(trace).merge(fill_value=None)
		self.stream = stream.copy()

	def run(self):
		"""

		"""
		global tf

		cft, maxcft = np.zeros(1), 0
		n = 0

		wait_pkts = (self.lta) / (tf / 1000)

		while n > 3:
			self.getq()
			n += 1
		n = 0

		while True:
			while True:
				if destinations[self.qno].qsize() > 0:
					self.getq()
				else:
					is_ch = self.getq()
					if is_ch:
						break

			if n > (wait_pkts):
				obstart = self.stream[0].stats.endtime - timedelta(
							seconds=self.lta)	# obspy time
				self.stream = self.stream.slice(
							starttime=obstart)	# slice the stream to the specified length (seconds variable)

				if self.filt:
					cft = recursive_sta_lta(self.stream[0].filter(
								type=self.filt, freq=self.freq,
								freqmin=self.freqmin, freqmax=self.freqmax),
								int(self.sta * self.sps), int(self.lta * self.sps))
				else:
					cft = recursive_sta_lta(self.stream[0],
							int(self.sta * self.sps), int(self.lta * self.sps))
				if cft.max() > self.thresh:
					if self.func == 'print':
						print()
						printM('Event detected! Trigger threshold: %s, CFT: %s '
								% (self.thresh, cft.max()), self.sender)
						printM('Waiting %s sec for clear trigger'
								% (self.lta), self.sender)
					else:
						print()
						printM('Trigger threshold of %s exceeded: %s'
								% (self.thresh, cft.max()), self.sender)
						self.func(*self.args, **self.kwargs)
					n = 1
				self.copy()

			elif n == 0:
				printM('Listening to channel %s'
						% (self.stream[0].stats.channel), self.sender)
				printM('Earthquake trigger warmup time of %s seconds...'
						% (self.lta), self.sender)
				n += 1
			elif n == (wait_pkts):
				if cft.max() == 0:
					printM('Earthquake trigger up and running normally.',
							self.sender)
				else:
					printM('Max CFT reached in alarm state: %s' % (maxcft),
							self.sender)
					printM('Earthquake trigger reset and active again.',
							self.sender)
					maxcft = 0
				n += 1
			else:
				if cft.max() > maxcft:
					maxcft = cft.max()
				n += 1


class WriteThread(Thread):
	def __init__(self, outdir='', stn=stn, debug=False):
		"""
		Initialize the thread
		"""
		super().__init__()
		global destinations

		wrteq = Queue(qsize)
		destinations.append(wrteq)
		self.qno = len(destinations) - 1

		self.stream = Stream()
		self.refcha = None
		self.outdir = outdir
		self.sender = 'WriteThread'
		self.debug = debug
		self.numchns = numchns
		self.stime = 1/sps
		printM('Starting.', self.sender)

	def getq(self):
		d = destinations[self.qno].get()
		destinations[self.qno].task_done()
		self.stream = update_stream(
			stream=self.stream, d=d, fill_value=None)
		if not self.refcha:
			self.refcha = getCHN(d)
		if self.refcha in str(d):
			return True
		else:
			return False
	
	###########
	#profiling#
	def on(self):
		self.pr = cProfile.Profile()
		self.pr.enable()

	def off(self):
		self.pr.disable()
		s = io.StringIO()
		sortby = SortKey.CUMULATIVE
		ps = pstats.Stats(self.pr, stream=s).sort_stats(sortby)
		printM('Printing CPU stats:', self.sender)
		ps.print_stats()
		print(s.getvalue())

	def elapsetime(self):
		self.lt = datetime.now()
	###########

	def copy(self):
		stream = Stream()
		for t in range(len(self.stream)):
			trace = Trace(data=self.stream[t].data)
			trace.stats.network = self.stream[t].stats.network
			trace.stats.location = self.stream[t].stats.location
			trace.stats.station = self.stream[t].stats.station
			trace.stats.channel = self.stream[t].stats.channel
			trace.stats.sampling_rate = self.stream[t].stats.sampling_rate
			trace.stats.starttime = self.stream[t].stats.starttime
			stream.append(trace).merge(fill_value=None)
		
		self.stream = stream.copy()


	def set_sps(self):
		self.sps = self.stream[0].stats.sampling_rate

	def elapse(self, new=False):
		self.st = UTCDateTime.now()
		self.y, self.m, self.d = self.st.year, self.st.month, self.st.day
		self.j = self.st.strftime('%j')
		self.newday = UTCDateTime(self.y, self.m, self.d + 1, 0, 0)
		if new:
			self.last = self.newday
		else:
			self.last = self.st

	def slicestream(self):
		self.stream.slice(starttime=self.last)

	def write(self, stream=False):
		if not stream:
			self.last = self.stream[0].stats.endtime - timedelta(seconds=5)
			stream = self.stream.copy().slice(
						endtime=self.last, nearest_sample=False)

		for t in stream:
			outfile = self.outdir + '/%s.%s.00.%s.D.%s.%s' % (t.stats.network,
								t.stats.station, t.stats.channel, self.y, self.j)
			if os.path.exists(os.path.abspath(outfile)):
				with open(outfile, 'ab') as fh:
					if self.debug:
						printM('Writing %s records to %s'
								% (len(t.data), outfile), self.sender)
					t.write(fh, format='MSEED', encoding='STEIM2')
			else:
				if self.debug:
					printM('Writing %s new file %s'
							% (len(t.data), outfile), self.sender)
				t.write(outfile, format='MSEED')

	def run(self):
		"""
		"""
		self.elapse()
		printM('miniSEED output directory: %s' % (self.outdir), self.sender)

		###########
		#profiling#
		self.on()
		self.lt = datetime.now()
		###########

		self.getq()
		self.set_sps()
		self.inv = get_inventory(stn=stn, sender=self.sender)
		if self.inv:
			printM('Writing inventory to output directory.', self.sender)
			inv.write('%s/%s.%s.00' % (self.outdir,
					  self.stream[0].stats.network,
					  self.stream[0].stats.station),
					  format='STATIONXML')
		printM('Beginning miniSEED output.', self.sender)
		wait_pkts = (self.numchns * 10) / (tf / 1000) 		# comes out to 10 seconds (tf is in ms)

		n = 0
		while True:
			while True:
				if destinations[self.qno].qsize() > 0:
					self.getq()
					n += 1
				else:
					self.getq()
					n += 1
					break
			if n >= wait_pkts:
				if self.newday < UTCDateTime.now(): # end of previous day and start of new day
					self.write(self.stream.slice(
								endtime=self.newday, nearest_sample=False))
					self.stream = self.stream.slice(
								starttime=self.newday, nearest_sample=False)
					self.elapse(new=True)
					###########
					#profiling#
					self.off()
					self.on()
					self.elapsetime()
					###########
				else:
					self.write()
					self.stream = self.stream.slice(
								starttime=self.last, nearest_sample=False)
				self.copy()
				n = 0


class PlotThread(Thread):
	def __init__(self, stn='Z0000', cha='all', seconds=30, spectrogram=False,
				 fullscreen=False):
		"""
		Initialize the thread
		"""
		super().__init__()
		global destinations

		plotq = Queue(qsize)
		destinations.append(plotq)
		self.qno = len(destinations) - 1
		self.stream = Stream()
		self.sender = 'PlotThread'
		printM('Starting.', self.sender)


	def getq(self):
		d = destinations[self.qno].get()
		destinations[self.qno].task_done()
		self.stream = update_stream(
			stream=self.stream.copy(), d=d, fill_value='latest')
	
	def set_sps(self):
		self.sps = self.stream[0].stats.sampling_rate

	def copy(self):
		stream = Stream()
		for t in range(len(self.stream)):
			trace = Trace(data=self.stream[t].data)
			trace.stats.network = self.stream[t].stats.network
			trace.stats.location = self.stream[t].stats.location
			trace.stats.station = self.stream[t].stats.station
			trace.stats.channel = self.stream[t].stats.channel
			trace.stats.sampling_rate = self.stream[t].stats.sampling_rate
			trace.stats.starttime = self.stream[t].stats.starttime
			stream.append(trace).merge(fill_value=None)
		self.stream = stream.copy()

	def setup_plot(self):
		pass

	def update_plot(self):
		pass

	def run(self):
		"""

		"""
		n = 0
		while n < 3:
			self.getq()
			n += 1
		self.set_sps()
		self.setup_plot()

		while True:
			while True:
				if destinations[self.qno].qsize() > 0:
					self.getq()
					n += 1
				else:
					self.getq()
					n += 1
					break
			self.copy()
			self.update_plot()


if __name__ == '__main__':
	pass