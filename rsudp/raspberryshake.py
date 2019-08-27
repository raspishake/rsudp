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

qsize = 120 			# max UDP queue size is 30 seconds' worth of seismic data
queue = Queue(qsize)	# master queue
destinations = []		# queues to write to

initd, sockopen = False, False
to = 10								# timeout
firstaddr = ''
inv = False

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

def initRSlib(dport=8888, rssta='Z0000', timeout=10):
	'''
	Set values for data port, station, network, and data port timeout prior to opening the socket.
	Defaults:
	dport=8888					# this is the port number to be opened
	rssta='Z0000'				# the name of the station (something like R0E05)
	timeout=10					# the number of seconds to wait for data before an error is raised (zero for unlimited wait)
	'''
	global port, sta, net, to, initd
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
		if len(rssta) == 5:
			sta = str(rssta).upper()
		else:
			sta = str(rssta).upper()
			printM('WARNING: Station name does not follow Raspberry Shake naming convention. Ignoring.')
	except ValueError as e:
		printM('ERROR: Invalid station name supplied.')
		printM('Error details: %s' % e)
	except Exception as e:
		printM('ERROR. Details:' % e)
	
	try:						# set timeout value 
		to = int(timeout)
	except ValueError as e:
		printM('ERROR: You likely supplied a non-integer as the timeout value. Your value: %s' % timeout)
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


def get_inventory(sta='Z0000'):
	global inv
	if 'Z0000' in sta:
		RS.printM('No station name given, continuing without inventory.')
		inv = False
	else:
		try:
			RS.printM('Fetching inventory for station %s.%s from Raspberry Shake FDSN.' % (RS.net, RS.sta))
			inv = read_inventory('https://fdsnws.raspberryshakedata.com/fdsnws/station/1/query?network=%s&station=%s&level=resp&format=xml'
								 % (RS.net, RS.sta))
			RS.printM('Inventory fetch successful.')
		except:
			RS.printM('Inventory fetch failed, continuing without.')
			inv = False


def make_trace(d):
	'''Makes a trace and assigns it some values using a data packet.'''
	ch = ['EHZ']#RS.getCHN(d)							# channel
	if ch:# in channels:
		t = getTIME(d)							# unix epoch time since 1970-01-01 00:00:00Z, or as obspy calls it, "timestamp"
		st = getSTREAM(d)						# samples in data packet in list [] format
		tr = Trace(data=np.ma.MaskedArray(st))		# create empty trace
		tr.stats.network = net						# assign values
		tr.stats.location = '00'
		tr.stats.station = sta
		tr.stats.channel = ch
		tr.stats.sampling_rate = 100#sps
		tr.stats.starttime = UTCDateTime(t)
		if inv:
			#try:
			tr.attach_response(inv)
			# except:
			# 	RS.printM('ERROR attaching inventory response. Are you sure you set the station name correctly?')
			# 	RS.printM('    This could indicate a mismatch in the number of data channels between the inventory and the stream.')
			# 	RS.printM('    For example, if you are receiving RS4D data, please make sure the inventory you download has 4 channels.')
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
	global destinations

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
	def __init__(self):
		"""
		Initialize the thread
		"""
		super().__init__()
		global destinations, alertqno

		alrtq = Queue(qsize)
		destinations.append(alrtq)
		alertqno = len(destinations) - 1

	def run(self):
		"""

		"""
		alert_stream = Stream()
		sta='R3BCF'
		#get_inventory(sta=sta)
		#if inv:
			#alert_stream.attach_response(inv)
		alert_stream.select(component='Z')

		tf = 4
		n = 0
		sta = 5
		lta = 10

		wait_pkts = tf * lta
		while True:
			while True:
				d = destinations[alertqno].get()
				destinations[alertqno].task_done()
				alert_stream = update_stream(
					stream=alert_stream, d=d, fill_value='latest')
				df = alert_stream[0].stats.sampling_rate
				break

			if n > (lta * tf):
				obstart = alert_stream[0].stats.endtime - timedelta(seconds=lta)	# obspy time
				alert_stream = alert_stream.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)

				cft = recursive_sta_lta(alert_stream[0], int(sta * df), int(lta * df))
				if cft.max() > 1.5:
				#cft = z_detect(alert_stream[0], int(sta * df))
				#if cft.max() > 1.1:
					printM('Event detected! CFT: %s (waiting %s sec for clear trigger)' % (cft.max(), lta))
					n = 1
				#else:
				#	RS.printM('                     CFT: %s' % (cft.max()))
			elif n == 0:
				printM('Earthquake trigger warmup time of %s seconds...' % (lta))
				n += 1
			elif n == (tf * lta):
				printM('Earthquake trigger up and running normally.')
				n += 1
			else:
				n += 1


class PlotThread(Thread):
	def __init__(self):
		"""
		Initialize the thread
		"""
		super().__init__()
		global destinations, plotqno

		plotq = Queue(qsize)
		destinations.append(prntq)
		plotqno = len(destinations) - 1

	def run(self):
		"""

		"""

		seconds = 30

		print_stream = Stream()
		sta='R3BCF'
		n = 0
		while True:
			d = destinations[plotqno].get()
			destinations[plotqno].task_done()
			alert_stream = update_stream(
				stream=alert_stream, d=d, fill_value='latest')
			df = alert_stream[0].stats.sampling_rate


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