import sys
import getopt
import datetime as dt
import signal
from . import raspberryshake

def signal_handler(signal, frame):
	print()
	raspberryshake.printM("Quitting...")
	sys.exit(0)
        
signal.signal(signal.SIGINT, signal_handler)

def printTTLS(CHAN, TR):
	'''
	Report packets lost.
	'''
	ttlSecs = int(DPtime[CHAN] - timeStart[CHAN])
	if ttlSecs == 0:
		return False		# only once in any given second
	ttlDPs = ttlSecs * TR
	pct = float(float(DPttlLoss[CHAN]) / float(ttlDPs)) * 100.
	raspberryshake.printM('CHANNEL %s: total packets lost in last %s seconds: %s ( %s%% / %s )' %
							(CHAN, ttlSecs, DPttlLoss[CHAN], round(pct, 2), ttlDPs))
	return True

def run(printFREQ=60, port=8888):
	'''
	Initialize stream and print constants, then process data for packet loss.
	'''
	raspberryshake.printM("Initializing...")
	raspberryshake.initRSlib(dport=port)
	raspberryshake.openSOCK()
	# initialize data stream constants
	raspberryshake.printM('Opened data port successfully.')
	DP = raspberryshake.getDATA()
	CHAN = raspberryshake.getCHN(DP)					# first channel - doesn't matter which, used to stop looping
	TR = raspberryshake.getTR(CHAN)						# transmission rate - in milliseconds
	TR = 1000 / TR							# number of DPs / second
	TRE = (TR+TR*.5) / 1000.				# time diff / error to identify a missed packet
	SR = raspberryshake.getSR(TR, DP)							# sample / second
	ttlCHN = raspberryshake.getTTLCHN()					# total number of channels
	raspberryshake.printM("	Total Channels: %s" % ttlCHN)
	raspberryshake.printM("	   Sample Rate: %s samples / second" % SR)
	raspberryshake.printM("	       TX Rate: Every %s milliseconds" % TR)
	
	# start processing data packets for packet loss detection
	# initialize
	chnNum = 0
	while chnNum < ttlCHN:
		DP = raspberryshake.getDATA()
		CHAN = raspberryshake.getCHN(DP)
		DPtime[CHAN] = raspberryshake.getTIME(DP)
		timeStart[CHAN] = DPtime[CHAN]
		DPttlLoss[CHAN] = 0
		chnNum += 1
	
	raspberryshake.printM('Data Packet reading begun.')
	raspberryshake.printM('Will report any DP loss as it happens and totals every %s seconds.' % printFREQ)

	while 1:                                # loop forever
		DP = raspberryshake.getDATA()
		CHAN = raspberryshake.getCHN(DP)
		timeS = raspberryshake.getTIME(DP)
		timeD = timeS - DPtime[CHAN]
		if abs(timeD) > TRE:
			raspberryshake.printM("DP loss of %s second(s) Current TS: %s, Previous TS: %s" % (round(timeD, 3), timeS, DPtime[CHAN]))
			DPttlLoss[CHAN] += abs(int(timeD * TR))
		DPtime[CHAN] = timeS 
	
		if int(timeS) % printFREQ == 0:
			if printTTLS(CHAN, TR):
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
##    $ python shake_udp_packetloss.py -p 18001 -f 3600                     ##
##                                                                          ##
##############################################################################

	'''

	f, p = 60, 8888
	opts, args = getopt.getopt(sys.argv[1:], 'hp:f:', ['help', 'port=', 'frequency='])
	for o, a in opts:
		if o in ('-h, --help'):
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
		raspberryshake.printM('Quitting...')


if __name__== "__main__":
	main()
