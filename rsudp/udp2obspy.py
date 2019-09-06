import sys, os
import getopt

import rsudp.raspberryshake as RS


def eqAlert(blanklines=True,
			printtext='Trigger threshold exceeded -- possible earthquake!',
			other='Waiting for clear trigger...'):
	printtext = str(printtext) + '\n' + str(other)
	RS.printM(printtext, sender='EQAlert function')


def main(alert=False, plot=False, debug=False, port=8888, stn='Z0000',
		 sta=5, lta=10, thresh=1.5, bp=False, cha='all', outdir='',
		 sec=30, spec=False, full=False, printdata=False, usage=False):

	prod = RS.ProducerThread(port=port, stn=stn)
	cons = RS.ConsumerThread()

	prod.start()
	cons.start()

	if printdata:
		prnt = RS.PrintThread()
		prnt.start()
	if alert:
		alrt = RS.AlertThread(sta=sta, lta=lta, thresh=thresh, bp=bp, func=eqAlert,
							  cha=cha, debug=debug)
		alrt.start()
	if plot:
		plotter = RS.PlotThread(stn=stn, cha=cha, seconds=sec, spectrogram=spec,
							 	fullscreen=full)
		plotter.start()
	if outdir:
		writer = RS.WriteThread(outdir=outdir, stn=stn, debug=debug)
		writer.start()

	if usage:
		usagetrack = RS.UsageThread(period=3600)
		usagetrack.start()

if __name__ == '__main__':
	'''
	Loads port, station, network, and duration arguments to create a graph.
	Supply -p, -s, -n, and/or -d to change the port and the output plot
	parameteRS.
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

		opts, args = getopt.getopt(sys.argv[1:], 'hvDp:s:n:d:c:PgfaS:L:T:o:U',
			['help', 'verbose', 'data', 'port=', 'station=', 'duration=', 'channels=', 'spectrogram',
			 'fullscreen', 'alarm', 'sta', 'lta', 'thresh', 'outdir=', 'usage']
			)
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
					RS.printM('ERROR: Could not set STA duration. Message: %s' % (a))
					exit(2)
			if o in ('-L', 'LTA='):
				try:
					lta = int(a)
				except ValueError as e:
					RS.printM('ERROR: Could not set LTA duration. Message: %s' % (a))
					exit(2)
			if o in ('-T', 'threshold='):
				try:
					thresh = float(a)
				except ValueError as e:
					RS.printM('ERROR: Could not set trigger threshold. Message: %s' % (a))
					exit(2)
			if o in ('-B', 'bandpass='):
				try:
					bp = list(a)
					bp = bp.sort()
				except ValueError as e:
					RS.printM('ERROR: Could not set bandpass limits. Message: %s' % (a))
					exit(2)
			if o in ('-o', 'outdir='):
				if os.path.isdir(os.path.abspath(a)):
					outdir = os.path.abspath(a)

		main(port=prt, stn=stn, cha=cha, sec=sec, spec=spec, full=full,
			 alert=alert, sta=sta, lta=lta, thresh=thresh, bp=bp,
			 debug=debug, printdata=printdata, outdir=outdir, plot=plot,
			 usage=usage)
	# except ValueError as e:
	# 	print('ERROR: %s' % e)
	# 	print(hlp_txt)
	# 	exit(2)
