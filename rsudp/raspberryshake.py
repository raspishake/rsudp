import sys
import socket as s
import datetime as dt
import signal
from threading import Thread
from queue import Queue
from obspy.core.trace import Trace
from obspy.core.stream import Stream
from obspy.signal.trigger import recursive_sta_lta
import numpy as np
from obspy import UTCDateTime
from datetime import datetime, timedelta
import time

qsize = 120 			# max UDP queue size is 30 seconds' worth of seismic data
queue = Queue(qsize)	# master queue
destinations = []		# queues to write to

initd, sockopen = False, False
to = 10					# socket test timeout
firstaddr = ''			# the first address data is received from
inv = False				# station inventory
producer, consumer = False, False # state of producer and consumer threads
stn = 'Z0000'			# station name
net = 'AM'				# network (this will always be AM)

tf = None				# transmission rate in ms
sps = None				# samples per second


def printM(msg):
	'''Prints messages with datetime stamp.'''
	print(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + msg)

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
	dport=8888					# this is the port number to be opened
	rsstn='Z0000'				# the name of the station (something like R0E05)
	timeout=10					# the number of seconds to wait for data before an error is raised (zero for unlimited wait)
	'''
	global port, stn, net, to, initd
	net = 'AM'
	initd = False				# initialization has not completed yet, therefore false
	try:						# set port value first
		if dport == int(dport):
			port = int(dport)
		else:
			port = int(dport)
			printM('WARNING: Supplied port value was converted to integer. Non-integer port numbers are invalid.')
	except ValueError as e:
		printM('ERROR: You likely supplied a non-integer as the port value. Your value: %s' % dport)
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
		printM('ERROR: You likely supplied a non-integer as the timeout value. Your value was: %s' % timeout)
		printM('       Continuing with default timeout of %s sec' % (to))
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
		printM("Opening socket on %s (HOST:PORT)" % HP)
		sock.bind((host, port))
		sockopen = True
	else:
		raise IOError("Before opening a socket, you must initialize this raspberryshake library by calling initRSlib(dport=XXXXX, rssta='R0E05') first.")

def test_connection():
	global to
	signal.signal(signal.SIGALRM, handler)
	signal.alarm(to)						# alarm time set with timeout value
	data, addr = sock.recvfrom(4096)
	signal.alarm(0)							# once data has been received, turn alarm completely off
	to = 0									# otherwise it erroneously triggers after keyboardinterrupt


def getDATA():
	'''Read a data packet off the port.
	Alarm if no data is received within timeout.'''
	global to, firstaddr
	notif = False
	if sockopen:
		signal.signal(signal.SIGALRM, handler)
		signal.alarm(to)						# alarm time set with timeout value
		data, addr = sock.recvfrom(4096)
		signal.alarm(0)							# once data has been received, turn alarm completely off
		to = 0									# otherwise it erroneously triggers after keyboardinterrupt
		if firstaddr == '':
			firstaddr = addr[0]
			printM('Receiving UDP data from %s' % (firstaddr))
		if (firstaddr != '') and (addr[0] == firstaddr):
			return data
		else:
			if notif == False:
				printM('Another address (%s) is sending UDP data to this port. Ignoring...' % (addr[0]))
				notif = True
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
	Timestamp is seconds since 1970-01-01 00:00:00Z, which can be passed directly to an obspy UTCDateTime object.
	Requires getDATA() packet as argument.'''
	return float(DP.split(b",")[1])

def getSTREAM(DP):
	'''Get the samples in a data packet as a list object.
	Requires getDATA() packet as argument.'''
	return list(map(int, DP.decode('utf-8').replace('}','').split(',')[2:]))

def getTR(chn):				# DP transmission rate in msecs
	'''Get the transmission rate in milliseconds.
	Requires a getCHN() or a channel name string as argument.'''
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
	return int(TR)

def getSR(TR, DP):
	'''Get the sample rate in samples per second.
	Requires an integer transmission rate and a data packet as arguments.'''
	return int((DP.count(b",") - 1) * 1000 / TR)
	
def getCHNS():
	'''Get a list of channels sent to the port.	'''
	chns = []
	chdict = {'EHZ': False, 'EHN': False, 'EHE': False, 'ENZ': False, 'ENN': False, 'ENE': False, 'HDF': False}
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
	return len(getCHNS())


def get_inventory(stn='Z0000'):
	global inv
	if 'Z0000' in stn:
		printM('No station name given, continuing without inventory.')
		inv = False
	else:
		try:
			printM('Fetching inventory for station %s.%s from Raspberry Shake FDSN.' % (net, sta))
			inv = read_inventory('https://fdsnws.raspberryshakedata.com/fdsnws/station/1/query?network=%s&station=%s&level=resp&format=xml'
								 % (net, stn))
			printM('Inventory fetch successful.')
		except:
			printM('Inventory fetch failed, continuing without.')
			inv = False


def make_trace(d):
	'''Makes a trace and assigns it some values using a data packet.'''
	ch = getCHN(d)							# channel
	if ch:# in channels:
		t = getTIME(d)							# unix epoch time since 1970-01-01 00:00:00Z, or as obspy calls it, "timestamp"
		st = getSTREAM(d)						# samples in data packet in list [] format
		tr = Trace(data=np.ma.MaskedArray(st))		# create empty trace
		tr.stats.network = net						# assign values
		tr.stats.location = '00'
		tr.stats.station = stn
		tr.stats.channel = ch
		tr.stats.sampling_rate = 100#sps
		tr.stats.starttime = UTCDateTime(t)
		if inv:
			try:
				tr.attach_response(inv)
			except:
				RS.printM('ERROR attaching inventory response. Are you sure you set the station name correctly?')
				RS.printM('    This could indicate a mismatch in the number of data channels between the inventory and the stream.')
				RS.printM('    For example, if you are receiving RS4D data, please make sure the inventory you download has 4 channels.')
		return tr

# Then make repeated calls to this, to continue adding trace data to the stream
def update_stream(stream, d, **kwargs):
	'''Returns an updated trace object with new data, merged down to one trace per available channel.'''
	while True:
		try:
			return stream.append(make_trace(d)).merge(**kwargs)
			return stream
		except TypeError:
			pass


class ProducerThread(Thread):
	def __init__(self, port, stn='Z0000'):
		"""
		Initialize the thread
		"""
		global destinations, producer

		if not producer:
			super().__init__()
			initRSlib(dport=port, rsstn=stn)
			openSOCK()
			test_connection()
			producer = True
		else:
			printM('Error: Producer thread already started')

	def run(self):
		"""
		Receives data from one IP address and puts it in an async queue.
		Prints each sending address to STDOUT so the user can troubleshoot.
		This will work best on local networks where a router does not obscure
		multiple devices behind one sending IP.
		Remember, UDP packets cannot be differentiated by sending instrument.
		Their identifiers are per channel (EHZ, HDF, ENE, SHZ, etc.)
		and not per Shake (R4989, R52CD, R24FA, RCB43, etc.). To avoid problems,
		please use a separate port for each Shake.
		"""
		global to
		global queue
		firstaddr = ''
		blocked = []
		printM('Waiting for UDP data on port %s...' % (port))
		while True:
			data, addr = sock.recvfrom(4096)
			if firstaddr == '':
				firstaddr = addr[0]
				printM('Receiving UDP data from %s' % (firstaddr))
			if (firstaddr != '') and (addr[0] == firstaddr):
				queue.put(data)
			else:
				if addr not in blocked:
					printM('Another IP (%s) is sending UDP data to this port. Ignoring...' % (addr[0]))
					blocked.append(addr)


class ConsumerThread(Thread):
	def __init__(self):
		"""
		Initialize the thread
		"""
		global destinations, consumer

		if not consumer:
			super().__init__()
		else:
			printM('Error: Consumer thread already started')

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


class AlertThread(Thread):
	def __init__(self, sta=5, lta=30, thresh=1.5, bp=False, func='print', printcft=True, *args, **kwargs):
		"""
		A recursive STA-LTA 
		:param str infile: Input DZT data file
		:param str outfile: Base output file name for plots, CSVs, and other products. Defaults to :py:data:`None`, which will cause the output filename to take a form similar to the input. The default will let the file be named via the descriptive naming function :py:data:`readgssi.functions.naming()`.
		"""
		super().__init__()
		global destinations, alertqno
		self.sta = sta
		self.lta = lta
		self.thresh = thresh
		self.func = func
		self.printcft = printcft
		self.args = args
		self.kwargs = kwargs
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
		alertqno = len(destinations) - 1

		printM('Starting Alert trigger thread with sta=%s and lta=%s' % (self.sta, self.lta))
		if self.filt == 'bandpass':
			printM('Alert stream will be %s filtered from %s to %s Hz' % (self.filt, self.freqmin, self.freqmax))
		elif self.filt in ('lowpass', 'highpass'):
			modifier = 'below' if self.filt in 'lowpass' else 'above'
			printM('Alert stream will be %s filtered %s %s Hz' % (self.filt, modifier, self.freq))
	def run(self):
		"""

		"""
		alert_stream = Stream()
		get_inventory(stn=stn)
		if inv:
			alert_stream.attach_response(inv)
		alert_stream.select(component='Z')

		cft, maxcft = np.zeros(1), 0
		tf = 4
		n = 0

		wait_pkts = tf * self.lta
		while True:
			while not destinations[alertqno].empty():
				d = destinations[alertqno].get()
				destinations[alertqno].task_done()
				alert_stream = update_stream(
					stream=alert_stream, d=d, fill_value='latest')
				df = alert_stream[0].stats.sampling_rate

			if n > (self.lta * tf):
				obstart = alert_stream[0].stats.endtime - timedelta(seconds=self.lta)	# obspy time
				alert_stream = alert_stream.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)

				if self.filt:
					cft = recursive_sta_lta(alert_stream[0].copy().filter(
								type=self.filt, freq=self.freq,
								freqmin=self.freqmin, freqmax=self.freqmax),
								int(self.sta * df), int(self.lta * df))
				else:
					cft = recursive_sta_lta(alert_stream[0], int(self.sta * df), int(self.lta * df))
				if cft.max() > self.thresh:
					if self.func == 'print':
						printM('Event detected! Trigger threshold: %s, CFT: %s ' % (thresh, cft.max()))
						printM('Waiting %s sec for clear trigger' % (lta))
					else:
						printM('Trigger threshold of %s exceeded: %s' % (thresh, cft.max()))
						self.func(*self.args, **self.kwargs)

					n = 1
			elif n == 0:
				printM('Earthquake trigger warmup time of %s seconds...' % (self.lta))
				n += 1
			elif n == (tf * self.lta):
				if cft.max() == 0:
					printM('Earthquake trigger up and running normally.')
				else:
					printM('Earthquake trigger reset and active again.')
					printM('Max CFT reached in alarm state: %s' % (maxcft))
					maxcft = 0
				n += 1
			else:
				if cft.max() > maxcft:
					maxcft = cft.max()
				n += 1


class PlotThread(Thread):
	def __init__(self, stn='Z0000', cha='all', seconds=30, spectrogram=False,
				 fullscreen=False):
		"""
		Initialize the thread
		"""
		super().__init__()
		global destinations, plotqno

		plotq = Queue(qsize)
		destinations.append(plotq)
		plotqno = len(destinations) - 1

	def run(self):
		"""

		"""
		print_stream = Stream()

		n = 0
		while not destinations[plotqno].empty():
			d = destinations[plotqno].get()
			destinations[plotqno].task_done()
			alert_stream = update_stream(
				stream=alert_stream, d=d, fill_value='latest')
			df = alert_stream[0].stats.sampling_rate
		time.wait(3)
		print('plotsdf')


class PrintThread(Thread):
	def __init__(self):
		"""
		Initialize the thread
		"""
		super().__init__()
		global destinations, printqno

		prntq = Queue(qsize)
		destinations.append(prntq)
		printqno = len(destinations) - 1

	def run(self):
		"""

		"""

		while True:
			d = destinations[printqno].get()
			destinations[printqno].task_done()
			print(str(d))