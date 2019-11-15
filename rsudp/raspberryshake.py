from datetime import datetime, timedelta
import time
import math
import numpy as np
import sys, os, platform
import socket as s
import signal
from obspy import UTCDateTime
from obspy.core.stream import Stream
from obspy import read_inventory
from obspy.core.trace import Trace
from rsudp import printM
from requests.exceptions import HTTPError

initd, sockopen = False, False
qsize = 2048 			# max queue size
port = 8888				# default listening port
to = 10					# socket test timeout
firstaddr = ''			# the first address data is received from
inv = False				# station inventory
producer = False 		# flag for producer status
stn = 'Z0000'			# station name
net = 'AM'				# network (this will always be AM)
chns = []				# list of channels
numchns = 0

tf = None				# transmission frequency in ms
tr = None				# transmission rate in packets per second
sps = None				# samples per second

# get an IP to report to the user
# from https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
def get_ip():
    testsock = s.socket(s.AF_INET, s.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        testsock.connect(('10.255.255.255', 1))
        IP = testsock.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        testsock.close()
    return IP

ip = get_ip()

# construct a socket
socket_type =  s.SOCK_DGRAM
sock = s.socket(s.AF_INET, socket_type)
if platform.system() not in 'Windows':
    sock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)

def handler(signum, frame, ip=ip):
	'''The signal handler for the nodata alarm.'''
	global port
	printM('ERROR: No data received in %s seconds; aborting.' % (to), sender='Init')
	printM('       Check that the Shake is forwarding data to:', sender='Init')
	printM('       IP address: %s    Port: %s' % (ip, port), sender='Init')
	printM('       and that no firewall exists between the Shake and this computer.', sender='Init')
	raise IOError('No data received')


def initRSlib(dport=port, rsstn='Z0000', timeout=10):
	'''
	Set values for data port, station, network, and data port timeout prior to opening the socket.
	Defaults:
	dport=8888		# this is the port number to be opened
	rsstn='Z0000'	# the name of the station (something like R0E05)
	timeout=10		# the number of seconds to wait for data before an error is raised (zero for unlimited wait)
	'''
	global port, stn, to, initd, port
	global producer
	sender = 'Init'
	printM('Initializing.', sender)
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
			printM('WARNING: Station name does not follow Raspberry Shake naming convention.')
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
	openSOCK()					# open a socket
	printM('Waiting for UDP data on port %s...' % (port), sender)
	set_params()				# get data and set parameters

def openSOCK(host=''):
	'''Initialize a socket at a port. Must be done after the initRSlib function is called.'''
	global sockopen
	sockopen = False
	if initd:
		HP = '%s:%s' % ('localhost',port)
		printM("Opening socket on %s (HOST:PORT)"
				% HP, 'openSOCK')
		try:
			sock.bind((host, port))
			sockopen = True
		except Exception as e:
			printM('ERROR:  Could not bind to port. Is another program using it?')
			printM('Detail: %s' % e)
			raise OSError(e)
	else:
		raise IOError("Before opening a socket, you must initialize this raspberryshake library by calling initRSlib(dport=XXXXX, rssta='R0E05') first.")

def set_params():
	'''Read a data packet off the port.
	On UNIX, alarm if no data is received within timeout.'''
	global to
	if os.name not in 'nt': 	# signal alarm not available on windows
		signal.signal(signal.SIGALRM, handler)
		signal.alarm(to)		# alarm time set with timeout value
	data = sock.recv(4096)
	if os.name not in 'nt':
		signal.alarm(0)			# once data has been received, turn alarm completely off
	to = 0						# otherwise it erroneously triggers after keyboardinterrupt
	getTR(getCHNS()[0])
	getSR(tf, data)
	getTTLCHN()
	printM('Available channels: %s' % chns, 'Init')
	get_inventory()

def getDATA():
	'''Read a data packet off the port.'''
	global to, firstaddr
	if sockopen:
		return sock.recv(4096)
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
	global tf, tr
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
	tr = int(1000 / TR)
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


def get_inventory(sender='get_inventory'):
	global inv, stn
	sender = 'get_inventory'
	if 'Z0000' in stn:
		printM('No station name given, continuing without inventory.',
				sender)
		inv = False
	else:
		try:
			printM('Fetching inventory for station %s.%s from Raspberry Shake FDSN.'
					% (net, stn), sender)
			
			inv = read_inventory('https://fdsnws.raspberryshakedata.com/fdsnws/station/1/query?network=%s&station=%s&starttime=%s&level=resp&nodata=404&format=xml'
								 % (net, stn, str(UTCDateTime.now()-timedelta(seconds=14400))))
			printM('Inventory fetch successful.', sender)
		except (IndexError, HTTPError):
			printM('WARNING: No inventory found for %s. Are you forwarding your Shake data?' % stn, sender)
			printM('         Deconvolution will only be available if data forwarding is on.', sender)
			printM('         Access the config page of the web front end for details.', sender)
			printM('         More info at https://manual.raspberryshake.org/quickstart.html', sender)
			inv = False
		except Exception as e:
			printM('ERROR: Inventory fetch failed!', sender)
			printM('       Error detail: %s' % e, sender)
			inv = False
	return inv


def make_trace(d):
	'''Makes a trace and assigns it some values using a data packet.'''
	global producer
	ch = getCHN(d)						# channel
	if ch:
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
				if producer:
					printM('ERROR: Could not attach inventory response.')
					print('                           Are you sure you set the station name correctly?')
					print('                           This could indicate a mismatch in the number of data channels')
					print('                           between the inventory and the stream. For example,')
					print('                           if you are receiving RS4D data, please make sure')
					print('                           the inventory you download has 4 channels.')
				producer = False
		return tr


# Then make repeated calls to this, to continue adding trace data to the stream
def update_stream(stream, d, **kwargs):
	'''Returns an updated trace object with new data, merged down to one trace per available channel.'''
	while True:
		try:
			return stream.append(make_trace(d)).merge(**kwargs)
		except TypeError:
			pass


def copy(orig):
	"""
	True copy a stream by creating a new stream and copying old attributes to it.
	This is necessary because the old stream accumulates *something* that causes
	CPU usage to increase over time as more data is added. This is a bug in obspy
	that I intend to find--or at the very least report--but until then this hack
	works fine.
	"""
	stream = Stream()
	for t in range(len(orig)):
		trace = Trace(data=orig[t].data)
		trace.stats.network = orig[t].stats.network
		trace.stats.location = orig[t].stats.location
		trace.stats.station = orig[t].stats.station
		trace.stats.channel = orig[t].stats.channel
		trace.stats.sampling_rate = orig[t].stats.sampling_rate
		trace.stats.starttime = orig[t].stats.starttime
		stream.append(trace).merge(fill_value=None)
	return stream.copy()


def deconvolve(self):
	self.stream = self.raw.copy()
	for trace in self.stream:
		trace.stats.units = self.units
		if self.deconv:
			if ('HZ' in trace.stats.channel) or ('HE' in trace.stats.channel) or ('HN' in trace.stats.channel):
				if self.deconv not in 'CHAN':
					trace.remove_response(inventory=inv, pre_filt=[0.1, 0.6, 0.95*self.sps, self.sps],
											output=self.deconv, water_level=4.5, taper=False)
				else:
					trace.remove_response(inventory=inv, pre_filt=[0.1, 0.6, 0.95*self.sps, self.sps],
											output='VEL', water_level=4.5, taper=False)
				if 'ACC' in self.deconv:
					trace.data = np.gradient(trace.data, 1)
				elif 'DISP' in self.deconv:
					trace.data = np.cumsum(trace.data)
					trace.taper(max_percentage=0.1, side='left', max_length=1)
					trace.detrend(type='demean')
				else:
					trace.stats.units = 'Velocity'
			elif ('NZ' in trace.stats.channel) or ('NE' in trace.stats.channel) or ('NN' in trace.stats.channel):
				if self.deconv not in 'CHAN':
					trace.remove_response(inventory=inv, pre_filt=[0.1, 0.6, 0.95*self.sps, self.sps],
											output=self.deconv, water_level=4.5, taper=False)
				else:
					trace.remove_response(inventory=inv, pre_filt=[0.1, 0.6, 0.95*self.sps, self.sps],
											output='ACC', water_level=4.5, taper=False)
				if 'VEL' in self.deconv:
					trace.data = np.cumsum(trace.data)
					trace.detrend(type='demean')
				elif 'DISP' in self.deconv:
					trace.data = np.cumsum(np.cumsum(trace.data))
					trace.detrend(type='linear')
				else:
					trace.stats.units = 'Acceleration'
				if ('ACC' not in self.deconv) and ('CHAN' not in self.deconv):
					trace.taper(max_percentage=0.1, side='left', max_length=1)

			else:
				trace.stats.units = 'Voltage counts'	# if this is HDF


if __name__ == '__main__':
	pass