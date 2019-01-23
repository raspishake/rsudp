import sys
import getopt
import datetime as dt
import signal
import rsh_udp.raspberryshake as RS

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
	RS.printM('CHANNEL %s: total packets lost in last %s seconds: %s ( %s%% / %s )' %
							(CHAN, ttlSecs, DPttlLoss[CHAN], round(pct, 2), ttlDPs))
	return True

def run(printFREQ=60, port=8888):
	'''
	Initialize stream and print constants, then process data for packet loss.
	'''
	RS.printM("Initializing...")
	RS.initRSlib(dport=port)
	RS.openSOCK()
	# initialize data stream constants
	RS.printM('Opened data port successfully.')
	DP = RS.getDATA()
	CHAN = RS.getCHN(DP)					# first channel - doesn't matter which, used to stop looping
	TR = RS.getTR(CHAN)						# transmission rate - in milliseconds
	TRS = 1000 / TR							# number of DPs / second
	TRE = (TR+TR*.5) / 1000.				# time diff / error to identify a missed packet
	SR = RS.getSR(TR, DP)							# sample / second
	ttlCHN = RS.getTTLCHN()					# total number of channels
	RS.printM("	Total Channels: %s" % ttlCHN)
	RS.printM("	   Sample Rate: %s samples / second" % SR)
	RS.printM("	       TX Rate: Every %s milliseconds" % TR)
	
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
	
	RS.printM('Data Packet reading begun.')
	RS.printM('Will report any DP loss as it happens and totals every %s seconds.' % printFREQ)

	while 1:                                # loop forever
		DP = RS.getDATA()
		CHAN = RS.getCHN(DP)
		timeS = RS.getTIME(DP)
		timeD = timeS - DPtime[CHAN]
		if abs(timeD) > TRE:
			RS.printM("DP loss of %s second(s) Current TS: %s, Previous TS: %s" % (round(timeD, 3), timeS, DPtime[CHAN]))
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

def main():
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
	try:
		run(printFREQ=f, port=p)
	except KeyboardInterrupt:
		print('')
		RS.printM('Quitting...')


if __name__== "__main__":
	main()
