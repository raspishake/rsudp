import sys
import getopt
import datetime as dt
import signal
import raspberryShake as RS

def signal_handler(signal, frame):
	print()
	RS.printM("Quitting...")
	sys.exit(0)
        
signal.signal(signal.SIGINT, signal_handler)

def printTTLS(CHAN, TRS):
	'''
	Report packets lost.
	'''
	ttlSecs = int(DPtime[CHAN] - timeStart[CHAN])
	if ttlSecs == 0:
		return False		# only once in any given second
	ttlDPs = ttlSecs * TRS
	pct = float(float(DPttlLoss[CHAN]) / float(ttlDPs)) * 100.
	RS.printM("CHANNEL " + str(CHAN.decode("utf-8")) + ": Total packets lost in last " + str(ttlSecs) + " seconds: " \
			+ str(DPttlLoss[CHAN]) \
			+ " ( " + str(round(pct, 2)) + "% / " + str(ttlDPs) + " )")
	return True

def main(printFREQ=60, port=8888):
	'''
	Initialize stream and print constants, then process data for packet loss.
	'''
	RS.printM("Initializing...")
	RS.initRSlib(dport=port)
	RS.openSOCK()
	# initialize data stream constants
	RS.printM('Opened data port successfully.')
	DP = RS.getDATA()
	CHAN = RS.getCHN(DP)						# first channel - doesn't matter which, used to stop looping
	TR = RS.getTR(CHAN)						# transmission rate - in milliseconds
	TRS = 1000 / TR							# number of DPs / second
	TRE = (TR+TR*.5) / 1000.				# time diff / error to identify a missed packet
	SR = RS.getSR(TR, DP)							# sample / second
	ttlCHN = RS.getTTLCHN()					# total number of channels
	RS.printM("	Total Channels: " + str(ttlCHN))
	RS.printM("	   Sample Rate: " + str(SR) + " samples / second")
	RS.printM("	       TX Rate: Every " + str(TR) + " milliseconds")
	
	# start processing data packets for packet loss detection
	# initialize
	chnNum = 0
	while chnNum < ttlCHN:
		DP = RS.getDATA()
		CHAN = RS.getCHN(DP)
		DPtime[CHAN] = RS.getTIME(DP)
		timeStart[CHAN] = DPtime[CHAN]
		DPttlLoss[CHAN] = 0
		chnNum += 1
	
	RS.printM("Data Packet reading begun... Will report any DP loss as it happens and totals every " \
			+ str(printFREQ) + " seconds")
	while 1:                                # loop forever
		DP = RS.getDATA()
		CHAN = RS.getCHN(DP)
		timeS = RS.getTIME(DP)
		timeD = timeS - DPtime[CHAN]
		if abs(timeD) > TRE:
			RS.printM("DP loss of " + str(round(timeD, 3)) + " second(s) " + \
					"Current TS: " + str(timeS) + ", Previous TS: " + str(DPtime[CHAN]))
			DPttlLoss[CHAN] += abs(int(timeD * TRS))
		DPtime[CHAN] = timeS 
	
		if int(timeS) % printFREQ == 0:
			if printTTLS(CHAN, TRS):
				timeStart[CHAN] = timeS
				DPttlLoss[CHAN] = 0

# some globals
DPtime = {}
timeStart = {}
DPttlLoss = {}

if __name__== "__main__":
	'''
	When run from the command line, pass in a value of seconds as an argument
	to set the packet loss for reporting period.

	for example, to report packet loss statistics every hour, run the following command:

	python shake-UDP-packetLoss.py -s 3600 -p 18001
	'''

	hlp_txt = '''
##############################################################################
##                       R A S P B E R R Y  S H A K E                       ##
##                         UDP Packet Loss Reporter                         ##
##                             by Richard Boaz                              ##
##                              Copyleft 2019                               ##
##                                                                          ##
## Reports data packet loss over a specified period of seconds.             ##
## Supply -p (port) and -f (frequency) to change the port and frequency     ##
## to report packet loss statistics.                                        ##
##                                                                          ##
## Requires:                                                                ##
## - raspberryShake                                                         ##
##                                                                          ##
## The following example sets the port to 18001 and report frequency        ##
## to 1 hour                                                                ##
##                                                                          ##
##############################################################################
##                                                                          ##
##    $ python live_example.py -p 18001 -f 3600                             ##
##                                                                          ##
##############################################################################

	'''

	f, p = 60, 8888
	opts, args = getopt.getopt(sys.argv[1:], 'hp:f:', ['help', 'port=', 'frequency='])
	for o, a in opts:
		if o in ('-h, --help'):
			h = True
			print(hlp_txt)
			exit(0)
		if o in ('-p', 'port='):
			p = int(a)
		if o in ('-f', 'frequency='):
			f = int(a)
	main(printFREQ=f, port=p)
