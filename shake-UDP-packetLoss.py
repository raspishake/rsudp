import sys
import datetime as dt
import signal
import raspberryShake as RS

def signal_handler(signal, frame):
	printM("Quitting...")
	sys.exit(0)
        
signal.signal(signal.SIGINT, signal_handler)

def printTTLS(CHAN, TRS):
	ttlSecs = int(DPtime[CHAN] - timeStart[CHAN])
	if ttlSecs == 0:
		return False		# only once in any given second
	ttlDPs = ttlSecs * TRS
	pct = float(float(DPttlLoss[CHAN]) / float(ttlDPs)) * 100.
	printM("CHANNEL " + CHAN + ": Total packets lost in last " + str(ttlSecs) + " seconds: " \
			+ str(DPttlLoss[CHAN]) \
			+ " ( " + str(round(pct, 2)) + "% / " + str(ttlDPs) + " )")
	return True

def main(printFREQ):
	RS.openSOCK(host, port)
	printM("Waiting for data on (HOST:PORT) " + HP)
	
	# initialize data stream constants
	printM("Initializing...")
	DP = RS.getDATA()
	CHAN = RS.getCHN(DP)						# first channel - doesn't matter which, used to stop looping
	TR = RS.getTR(CHAN)						# transmission rate - in milliseconds
	TRS = 1000 / TR							# number of DPs / second
	TRE = (TR+TR*.5) / 1000.				# time diff / error to identify a missed packet
	SR = RS.getSR(TR)							# sample / second
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
	if len(sys.argv) != 2:
		RS.printM("Argument required: frequency to print totals, in seconds")
		sys.exit(0)
		
	printFREQ = int(sys.argv[1])		# how often to print loss totals, in seconds
	main(printFREQ)
