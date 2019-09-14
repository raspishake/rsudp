import sys, os
import signal
import getopt
import time
import rsudp.raspberryshake as RS

running = False

def eqAlert(blanklines=True,
			printtext='Trigger threshold exceeded -- possible earthquake!',
			other='Waiting for clear trigger...'):
	printtext = str(printtext) + '\n' + str(other)
	RS.printM(printtext, sender='EQAlert function')

def prod():
	global running
	sender = 'Producer'
	chns = []
	numchns = 0

	"""
	Receives data from one IP address and puts it in an async queue.
	Prints each sending address to STDOUT so the user can troubleshoot.
	This will work best on local networks where a router does not obscure
	multiple devices behind one sending IP.
	Remember, RS UDP packets cannot be differentiated by sending instrument.
	Their identifiers are per channel (EHZ, HDF, ENE, SHZ, etc.)
	and not per Shake (R4989, R52CD, R24FA, RCB43, etc.). To avoid problems,
	please use a separate port for each Shake.
	"""
	firstaddr = ''
	blocked = []
	running = True
	while running:
		data, addr = RS.sock.recvfrom(4096)
		if firstaddr == '':
			firstaddr = addr[0]
			RS.printM('Receiving UDP data from %s' % (firstaddr), sender)
		if (firstaddr != '') and (addr[0] == firstaddr):
			RS.queue.put(data)
		else:
			if addr[0] not in blocked:
				RS.printM('Another IP (%s) is sending UDP data to this port. Ignoring...'
						% (addr[0]), sender)
				blocked.append(addr[0])
	
	print()
	RS.printM('Sending TERM signal to processes...', sender)
	RS.queue.put(b'TERM')
	RS.queue.join()

def handler(sig, frame):
	global running
	running = False

def run(alert=False, plot=False, debug=False, port=8888, stn='Z0000',
		 sta=5, lta=10, thresh=1.5, bp=False, cha='all', outdir='',
		 sec=30, spec=False, full=False, printdata=False, usage=False):

	# handler for the exit signal
	signal.signal(signal.SIGINT, handler)

	RS.initRSlib(dport=port, rsstn=stn)

	cons = RS.Consumer()

	cons.start()

	if printdata:
		prnt = RS.Print()
		prnt.start()
	if alert:
		alrt = RS.Alert(sta=sta, lta=lta, thresh=thresh, bp=bp, func=eqAlert,
							  cha=cha, debug=debug)
		alrt.start()
	if outdir:
		writer = RS.Write(outdir=outdir, stn=stn, debug=debug)
		writer.start()

	if plot and RS.mpl:
		while True:
			if RS.numchns == 0:
				time.sleep(0.01)
				continue
			else:
				break
		plotter = RS.Plot(stn=stn, cha=cha, seconds=sec, spectrogram=spec,
								fullscreen=full)
		plotter.start()

	prod()

	for q in RS.destinations:
		q.join()
	for p in RS.multiprocessing.active_children():
		p.terminate()
	RS.printM('Shutdown successful.', 'Main')
	sys.exit(0)


def main():
	'''
	Loads port, station, network, and duration arguments to create a graph.
	Supply -p, -s, -n, and/or -d to change the port and the output plot
	parameters.
	'''

	hlp_txt='''
##############################################################################
##                       R A S P B E R R Y  S H A K E                       ##
##                             UDP Data Library                             ##
##                              by Ian Nesbitt                              ##
##                              Copyleft  2019                              ##
##                                                                          ##
## Loads port, station, and duration arguments to create a graph.           ##
## Supply -p, -s, and/or -d to change the port and the output plot          ##
## parameteRS. Use -g to plot spectrogram(s).                               ##
##                                                                          ##
## Requires:                                                                ##
## - Numpy                                                                  ##
## - ObsPy                                                                  ##
## - Matplotlib                                                             ##
## - rsudp                                                                  ##
##                                                                          ##
## The following example sets the port to 18001, station to R0E05,          ##
## and plot duration to 25 seconds, then plots data live with spectrogram:  ##
##                                                                          ##
##############################################################################
##                                                                          ##
##    $ python live_example.py -p 18001 -s R0E05 -d 25 -g                   ##
##                                                                          ##
##############################################################################

	'''

	if True: #try:
		prt, stn, sec, cha = 8888, 'Z0000', 30, 'all'
		h = False
		debug = False
		full, spec = False, False
		printdata = False
		alert = False
		plot = False
		bp = False	# (can be tuple or list)
		outdir = False
		usage = False

		# short term average / long term average (STA/LTA) noise trigger defaults
		sta, lta = 6, 30	# short term & long term period for alert (seconds)
		thresh = 1.6		# threshold for STA/LTA

		opts = getopt.getopt(sys.argv[1:], 'hvDp:s:n:d:c:PgfaS:L:T:o:U',
			['help', 'verbose', 'data', 'port=', 'station=', 'duration=', 'channels=', 'spectrogram',
			 'fullscreen', 'alarm', 'sta', 'lta', 'thresh', 'outdir=', 'usage']
			)[0]
		for o, a in opts:
			if o in ('-h, --help'):
				h = True
				print(hlp_txt)
				exit(0)
			if o in ('-v', '--verbose'):
				debug = True
			if o in ('-D', '--data'):
				printdata = True
			if o in ('-U', '--usage'):
				usage = True
			if o in ('-p', 'port='):
				prt = int(a)
			if o in ('-s', 'station='):
				stn = str(a)
			if o in ('-c', 'channels='):
				cha = a.split(',')
			if o in ('-d', 'duration='):
				sec = int(a)
			if o in ('-g', '--spectrogram'):
				spec = True
			if o in ('-f', '--fullscreen'):
				full = True
			if o in ('-P', '--plot'):
				plot = True
			if o in ('-a', '--alert'):
				alert = True
			if o in ('-S', 'STA='):
				try:
					sta = int(a)
				except ValueError as e:
					RS.printM('ERROR: Could not set STA duration to %s. Message: %s' % (a, e))
					exit(2)
			if o in ('-L', 'LTA='):
				try:
					lta = int(a)
				except ValueError as e:
					RS.printM('ERROR: Could not set LTA duration to %s. Message: %s' % (a, e))
					exit(2)
			if o in ('-T', 'threshold='):
				try:
					thresh = float(a)
				except ValueError as e:
					RS.printM('ERROR: Could not set trigger threshold to %s. Message: %s' % (a, e))
					exit(2)
			if o in ('-B', 'bandpass='):
				try:
					bp = list(a)
					bp = bp.sort()
				except ValueError as e:
					RS.printM('ERROR: Could not set bandpass limits to %s. Message: %s' % (a, e))
					exit(2)
			if o in ('-o', 'outdir='):
				if os.path.isdir(os.path.abspath(a)):
					outdir = os.path.abspath(a)

		run(port=prt, stn=stn, cha=cha, sec=sec, spec=spec, full=full,
			alert=alert, sta=sta, lta=lta, thresh=thresh, bp=bp,
			debug=debug, printdata=printdata, outdir=outdir, plot=plot,
			usage=usage)

if __name__ == '__main__':
	main()
