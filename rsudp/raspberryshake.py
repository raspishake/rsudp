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
import math
try:
	import matplotlib.pyplot as plt
	import linecache
except:
	printM('ERROR: Could not import matplotlib, plotting will not be available')


qsize = 2048 			# max queue size
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

# from https://docs.obspy.org/_modules/obspy/imaging/spectrogram.html#_nearest_pow_2:
def _nearest_pow_2(x):
    """
    Find power of two nearest to x

    >>> _nearest_pow_2(3)
    2.0
    >>> _nearest_pow_2(15)
    16.0

    :type x: float
    :param x: Number
    :rtype: Int
    :return: Nearest power of 2 to x

    Adapted from the obspy library
    """
    a = math.pow(2, math.ceil(np.log2(x)))
    b = math.pow(2, math.floor(np.log2(x)))
    if abs(a - x) < abs(b - x):
        return a
    else:
        return b


class ProducerThread(Thread):
	def __init__(self, port, stn='Z0000'):
		"""
		Initialize the thread
		"""
		super().__init__()
		self.sender = 'ProducerThread'
		self.chns = []
		self.numchns = 0

		printM('Starting.', self.sender)
		initRSlib(dport=port, rsstn=stn)
		openSOCK()
		printM('Waiting for UDP data on port %s...' % (port), self.sender)
		test_connection()
		self.sps = sps
		self.chns = chns
		self.numchns = numchns

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
		super().__init__()
		global destinations
		destinations = []
		self.active = False

		self.sender = 'ConsumerThread'
		printM('Starting.', self.sender)

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
				if self.getq():
					n += 1
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
					time.sleep(0.005)		# wait a few ms to see if another packet will arrive
				else:
					break
			if n >= wait_pkts:
				if self.newday < UTCDateTime.now(): # end of previous day and start of new day
					self.write(self.stream.slice(
								endtime=self.newday, nearest_sample=False))
					self.stream = self.stream.slice(
								starttime=self.newday, nearest_sample=False)
					self.elapse(new=True)
				else:
					self.write()
					self.stream = self.stream.slice(
								starttime=self.last, nearest_sample=False)
				self.copy()
				n = 0

				self.getq()
				time.sleep(0.005)		# wait a few ms to see if another packet will arrive


class PlotThread(Thread):
	def __init__(self, num_chans, stn='Z0000', cha='all',
				 seconds=30, spectrogram=False,
				 fullscreen=False, qt=True):
		"""
		Initialize the plot thread


		"""
		super().__init__()
		global destinations

		plotq = Queue(qsize)
		destinations.append(plotq)
		self.qno = len(destinations) - 1
		self.stream = Stream()
		self.sender = 'PlotThread'
		self.stn = stn
		self.net = net
		self.cha = cha
		self.chans = chns
		self.seconds = seconds
		self.spectrogram = spectrogram
		self.per_lap = 0.9
		self.fullscreen = fullscreen
		self.qt = qt
		self.num_chans = num_chans
		self.delay = 2 if self.num_chans > 1 else 1
		# plot stuff
		self.bgcolor = '#202530' # background
		self.fgcolor = '0.8' # axis and label color
		self.linecolor = '#c28285' # seismogram color
		printM('Starting.', self.sender)

	def getq(self):
		d = destinations[self.qno].get()
		destinations[self.qno].task_done()
		self.stream = update_stream(
			stream=self.stream, d=d, fill_value='latest')
	
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

	def _nearest_pow_2(self, x):
		"""
		Find power of two nearest to x

		>>> _nearest_pow_2(3)
		2.0
		>>> _nearest_pow_2(15)
		16.0

		:type x: float
		:param x: Number
		:rtype: Int
		:return: Nearest power of 2 to x

		Adapted from the obspy library
		"""
		a = math.pow(2, math.ceil(np.log2(x)))
		b = math.pow(2, math.floor(np.log2(x)))
		if abs(a - x) < abs(b - x):
			return a
		else:
			return b

	def setup_plot(self):
		"""
		Matplotlib is not threadsafe, so things are a little weird here.
		"""
		# instantiate a figure and set basic params
		self.fig = plt.figure(figsize=(8,3*self.num_chans))
		self.fig.patch.set_facecolor(self.bgcolor)	# background color
		self.fig.suptitle('Raspberry Shake station %s.%s live output' # title
					% (self.net, self.stn), fontsize=14, color=self.fgcolor)
		self.ax, self.lines = [], []				# list for subplot axes and lines artists
		self.mult = 1					# spectrogram selection multiplier
		if self.spectrogram:
			self.mult = 2				# 2 if user wants a spectrogram else 1
			if self.seconds > 60:
				self.per_lap = 0.9		# if axis is long, spectrogram overlap can be shorter
			else:
				self.per_lap = 0.975	# if axis is short, increase resolution
			# set spectrogram parameters
			self.nfft1 = self._nearest_pow_2(self.sps)
			self.nlap1 = self.nfft1 * self.per_lap

		for i in range(self.num_chans):
			if i == 0:
				# set up first axes (axes added later will share these x axis limits)
				self.ax.append(self.fig.add_subplot(self.num_chans*self.mult,
							   1, 1, label=str(1)))
				self.ax[0].set_facecolor(self.bgcolor)
				self.ax[0].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)
				if self.spectrogram:
					self.ax.append(self.fig.add_subplot(self.num_chans*self.mult,
								   1, 2, label=str(2)))#, sharex=ax[0]))
					self.ax[1].set_facecolor(self.bgcolor)
					self.ax[1].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)
			else:
				# add axes that share either lines or spectrogram axis limits
				s = i * self.mult	# plot selector
				# add a subplot then set colors
				self.ax.append(self.fig.add_subplot(self.num_chans*self.mult,
							   1, s+1, sharex=self.ax[0], label=str(s+1)))
				self.ax[s].set_facecolor(self.bgcolor)
				self.ax[s].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)
				if self.spectrogram:
					# add a spectrogram and set colors
					self.ax.append(self.fig.add_subplot(self.num_chans*self.mult,
								   1, s+2, sharex=self.ax[1], label=str(s+2)))
					self.ax[s+1].set_facecolor(self.bgcolor)
					self.ax[s+1].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)

		for axis in self.ax:
			# set the rest of plot colors
			plt.setp(axis.spines.values(), color=self.fgcolor)
			plt.setp([axis.get_xticklines(), axis.get_yticklines()], color=self.fgcolor)

		# calculate times
		obstart = self.stream[0].stats.endtime - timedelta(seconds=self.seconds)	# obspy time
		start = np.datetime64(self.stream[0].stats.endtime
							  )-np.timedelta64(self.seconds, 's')	# numpy time
		end = np.datetime64(self.stream[0].stats.endtime)	# numpy time

		# set up axes and artists
		for i in range(self.num_chans): # create lines objects and modify axes
			if len(self.stream[i].data) < int(self.sps*(1/self.per_lap)):
				comp = 0				# spectrogram offset compensation factor
			else:
				comp = 1/self.per_lap	# spectrogram offset compensation factor
			r = np.arange(start, end, np.timedelta64(int(1000/self.sps), 'ms'))[-len(
						  self.stream[i].data[int(-self.sps*(self.seconds-(comp/2))):-int(self.sps*(comp/2))]):]
			mean = int(round(np.mean(self.stream[i].data)))
			# add artist to lines list
			self.lines.append(self.ax[i*self.mult].plot(r,
							  np.nan*(np.zeros(len(r))),
							  label=self.stream[i].stats.channel, color=self.linecolor,
							  lw=0.45)[0])
			# set axis limits
			self.ax[i*self.mult].set_xlim(left=start.astype(datetime),
										  right=end.astype(datetime))
			self.ax[i*self.mult].set_ylim(bottom=np.min(self.stream[i].data-mean)
										  -np.ptp(self.stream[i].data-mean)*0.1,
										  top=np.max(self.stream[i].data-mean)
										  +np.ptp(self.stream[i].data-mean)*0.1)
			# we can set line plot labels here, but not imshow labels
			self.ax[i*self.mult].set_ylabel('Voltage counts', color=self.fgcolor)
			self.ax[i*self.mult].legend(loc='upper left')	# legend and location
			if self.spectrogram:		# if the user wants a spectrogram, plot it
				# add spectrogram to axes list
				sg = self.ax[1].specgram(self.stream[i].data, NFFT=8, pad_to=8,
										 Fs=self.sps, noverlap=7, cmap='inferno',
										 xextent=(self.seconds-0.5, self.seconds))[0]
				self.ax[1].set_xlim(0,self.seconds)
				self.ax[i*self.mult+1].set_ylim(0,int(self.sps/2))

		# update canvas and draw
		if self.fullscreen: # set up fullscreen
			figManager = plt.get_current_fig_manager()
			if self.qt:	# try maximizing in Qt first
				figManager.window.showMaximized()
			else:	# if Qt fails, try Tk
				figManager.resize(*figManager.window.maxsize())

		plt.draw()									# draw the canvas
		self.fig.canvas.start_event_loop(0.005)		# wait for canvas to update
		if self.fullscreen:		# carefully designed plot layout parameters
			plt.tight_layout(pad=0, rect=[0.015, 0.01, 0.99, 0.955])	# [left, bottom, right, top]
		else:	# carefully designed plot layout parameters
			plt.tight_layout(pad=0, h_pad=0.1, w_pad=0,
							 rect=[0.015, 0.01, 0.99, 0.885+(0.02*self.num_chans)])	# [left, bottom, right, top]

	def update_plot(self):
		obstart = self.stream[0].stats.endtime - timedelta(seconds=self.seconds)	# obspy time
		start = np.datetime64(self.stream[0].stats.endtime
							  )-np.timedelta64(self.seconds, 's')	# numpy time
		end = np.datetime64(self.stream[0].stats.endtime)	# numpy time
		self.stream = self.stream.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)
		i = 0
		for i in range(self.num_chans):	# for each channel, update the plots
			comp = 1/self.per_lap	# spectrogram offset compensation factor
			r = np.arange(start, end, np.timedelta64(int(1000/self.sps), 'ms'))[-len(
						self.stream[i].data[int(-self.sps*(self.seconds-(comp/2))):-int(self.sps*(comp/2))]):]
			mean = int(round(np.mean(self.stream[i].data)))
			self.lines[i].set_ydata(self.stream[i].data[int(-self.sps*(self.seconds-(comp/2))):-int(self.sps*(comp/2))]-mean)
			self.lines[i].set_xdata(r)	# (1/self.per_lap)/2
			self.ax[i*self.mult].set_xlim(left=start.astype(datetime)+timedelta(seconds=comp*1.5),
										  right=end.astype(datetime))
			self.ax[i*self.mult].set_ylim(bottom=np.min(self.stream[i].data-mean)
										  -np.ptp(self.stream[i].data-mean)*0.1,
										  top=np.max(self.stream[i].data-mean)
										  +np.ptp(self.stream[i].data-mean)*0.1)
			if self.spectrogram:
				self.nfft1 = self._nearest_pow_2(self.sps)	# FFTs run much faster if the number of transforms is a power of 2
				self.nlap1 = self.nfft1 * self.per_lap
				if len(self.stream[i].data) < self.nfft1:	# when the number of data points is low, we just need to kind of fake it for a few fractions of a second
					self.nfft1 = 8
					self.nlap1 = 6
				sg = self.ax[i*self.mult+1].specgram(self.stream[i].data-mean,
							NFFT=self.nfft1, pad_to=int(self.sps*4),
							Fs=self.sps, noverlap=self.nlap1)[0]	# meat & potatoes
				self.ax[i*self.mult+1].clear()	# incredibly important, otherwise continues to draw over old images (gets exponentially slower)
				# cloogy way to shift the spectrogram to line up with the seismogram
				self.ax[i*self.mult+1].set_xlim(0.25,self.seconds-0.25)
				self.ax[i*self.mult+1].set_ylim(0,int(self.sps/2))
				# imshow to update the spectrogram
				self.ax[i*self.mult+1].imshow(np.flipud(sg**(1/float(10))), cmap='inferno',
						extent=(self.seconds-(1/(self.sps/float(len(self.stream[i].data)))),
								self.seconds,0,self.sps/2), aspect='auto')
				# some things that unfortunately can't be in the setup function:
				self.ax[i*self.mult+1].tick_params(axis='x', which='both',
						bottom=False, top=False, labelbottom=False)
				self.ax[i*self.mult+1].set_ylabel('Frequency (Hz)', color=self.fgcolor)
				self.ax[i*self.mult+1].set_xlabel('Time (UTC)', color=self.fgcolor)
			else:
				# also can't be in the setup function
				self.ax[i*self.mult].set_xlabel('Time (UTC)', color=self.fgcolor)

	def loop(self):
		"""
		Let some time elapse in order for the plot canvas to draw properly.
		Must be separate from :func:`update_plot()` to avoid a broadcast error early in plotting.
		Takes no arguments except :py:code:`self`.
		"""
		self.fig.canvas.start_event_loop(0.005)

	def run(self):
		"""
		The heart of the plotting routine.

		Begins by updating the queue to populate a :py:`obspy.core.stream.Stream` object, then setting up the main plot.
		The first time through the main loop, the plot is not drawn. After that, the plot is drawn every time all channels are updated.
		Any plots containing a spectrogram and more than 1 channel are drawn at most every half second (500 ms).
		All other plots are drawn at most every quarter second (250 ms).
		"""
		self.getq() # block until data is flowing from the consumer
		self.set_sps()
		for i in range((self.num_chans-1)*2): # fill up a stream object
			self.getq()

		self.setup_plot()
		i = 0	# number of plot events
		u = -1	# number of queue calls
		while True: # main loop
			while True:
				if destinations[self.qno].qsize() > 0:
					self.getq()
					u += 1
					time.sleep(0.001)		# wait a ms to see if another packet will arrive
				else:
					if int(u/(self.num_chans*self.delay)) == float(u/(self.num_chans*self.delay)):
						u = 0
						break

			if i > 10:
				linecache.clearcache()
				i = 0
			else:
				i += 1
			self.copy()
			self.update_plot()
			if u >= 0:				# avoiding a matplotlib broadcast error
				self.loop()

			self.getq()
			u += 1
			time.sleep(0.001)		# wait a ms to see if another packet will arrive


if __name__ == '__main__':
	pass