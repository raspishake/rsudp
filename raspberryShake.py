import sys
import socket as s
import datetime as dt
import signal

def printM(msg):
	print dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + msg

initV = 0.0
initVS = ""

host = initVS                           # when running not on the Shake Pi: blank = localhost 
port = 32768                            # Port to bind to
sock = initVS

def openSOCK()
	if host == initVS:
		HP = "localhost:" + str(port)
	else:
		HP = host + ":" + str(port)
	printM("Opening socket on (HOST:PORT) " + HP)
	
	sock = s.socket(s.AF_INET, s.SOCK_DGRAM | s.SO_REUSEADDR)
	sock.bind((host, port))

def getDATA():				# read a DP off the port
	data, addr = sock.recvfrom(1024)
	return data
	
def getCHN(DP):				# extract the channel from the DP
	return DP.split(",")[0][1:]
	
def getTIME(DP):			# extract the timestamp
	return float(DP.split(",")[1])
	
def getTR(chn):				# DP transmission rate in msecs
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

def getSR(TR):				# sample rate - samples / second
	DP = getDATA()
	return int((DP.count(",") - 1) * 1000 / TR)
	
def getTTLCHN():
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

