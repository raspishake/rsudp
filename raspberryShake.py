import sys
import socket as s
import datetime as dt
import signal

def printM(msg):
	'''Prints messages with datetime stamp.'''
	print(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + msg)

initV = 0.0
initVS = ""

timeout = 15							# time to wait for data
host = initVS                           # should always revert to localhost
sock = s.socket(s.AF_INET, s.SOCK_DGRAM | s.SO_REUSEADDR)

def handler(signum, frame):
	'''The signal handler for the nodata alarm.'''
	printM('No data received in %s seconds; aborting.' % (timeout))
	printM('Check that the data is being forwarded to the local port correctly.')
	raise IOError('No data received')

def openSOCK(host='localhost', port=8888):
	'''Initialize a socket at a port. Port defaults to 8888. Pass another local port value to change.'''
	if host == initVS:
		HP = "localhost:" + str(port)
	else:
		HP = host + ":" + str(port)
	printM("Opening socket on (HOST:PORT) " + HP)
	
	sock.bind((host, port))

def getDATA():
	'''Read a data packet off the port.
	Alarm if no data is received within timeout.'''
	signal.signal(signal.SIGALRM, handler)
	signal.alarm(timeout)
	data, addr = sock.recvfrom(1024)
	signal.alarm(0)
	return data
	
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
	timeP1 = initV
	timeP2 = initV
	done = False
	while not done:
		DP = getDATA()
		CHAN = getCHN(DP)
		if CHAN == chn:
			if timeP1 == initV:
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
	
def getTTLCHN():
	'''Calculate total number of channels received.'''
	firstCHN = initVS
	ttlchn = 0
	done = False
	while not done:
		DP = getDATA()
		if firstCHN == initVS:
			firstCHN = getCHN(DP)
			ttlchn = 1
			continue
		nextCHN = getCHN(DP)
		if firstCHN == nextCHN:
			done = True
			continue
		ttlchn += 1
	return ttlchn

def getCHNS():
	'''Get a list of channels sent to the port.	'''
	chns = []
	firstCHN = initVS
	done = False
	while not done:
		DP = getDATA()
		if firstCHN == initVS:
			firstCHN = getCHN(DP)
			chns.append(firstCHN)
			continue
		nextCHN = getCHN(DP)
		if firstCHN == nextCHN:
			done = True
			continue
		else:
			chns.append(nextCHN)
	return chns