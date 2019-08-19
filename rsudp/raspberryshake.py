import sys
import socket as s
import datetime as dt
import signal

initd, sockopen = False, False
to = 10								# timeout
firstaddr = ''

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
		printM("Opening socket on (HOST:PORT) %s" % HP)	
		sock.bind((host, port))
		sockopen = True
	else:
		raise IOError("Before opening a socket, you must initialize this raspberryshake library by calling initRSlib(dport=XXXXX, rssta='R0E05') first.")


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
