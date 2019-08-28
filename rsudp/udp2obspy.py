import rsudp.raspberryshake as RS


def eqAlert(blanklines=True,
			printtext='Trigger threshold exceeded -- possible earthquake!',
			other=''):
	if blanklines:
		printtext = '\n' + str(printtext) + '\n'
	RS.printM(printtext)

def main(alert=True, plot=False, print=False, port=8888, stn='Z0000',
		 sta=5, lta=10, thresh=1.5, bp=False, cha='all',
		 sec=30, spec=False, full=False):

	prod = RS.ProducerThread(port=port, stn=stn)
	cons = RS.ConsumerThread()

	prod.start()
	cons.start()

	if alert:
		alrt = RS.AlertThread(sta=sta, lta=lta, thresh=thresh, func=tweet)
		alrt.start()
	if stdprint:
		prnt = RS.PrintThread()
		prnt.start()
	if plotting:
		plot = RS.PlotThread(stn=stn, cha=cha, seconds=sec, spectrogram=spec
							 fullscreen=full)
		plot.start()

if __name__ == '__main__':
def main():
	'''
	Loads port, station, network, and duration arguments to create a graph.
	Supply -p, -s, -n, and/or -d to change the port and the output plot
	parameters.
	'''

	hlp_txt='''
##############################################################################
##                       R A S P B E R R Y  S H A K E                       ##
##                         UDP Data Plotter Example                         ##
##                              by Ian Nesbitt                              ##
##                              Copyleft  2019                              ##
##                                                                          ##
## Loads port, station, and duration arguments to create a graph.           ##
## Supply -p, -s, and/or -d to change the port and the output plot          ##
## parameters. Use -g to plot spectrogram(s).                               ##
##                                                                          ##
## Requires:                                                                ##
## - Numpy                                                                  ##
## - ObsPy                                                                  ##
## - Matplotlib                                                             ##
## - rs2obspy                                                               ##
## - raspberryShake                                                         ##
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
		full, spec = False, False
		opts, args = getopt.getopt(sys.argv[1:], 'hp:s:n:d:c:gfaS:L:T:',
			['help', 'port=', 'station=', 'duration=', 'channels=', 'spectrogram',
			 'fullscreen', 'alarm', 'sta', 'lta']
			)
		for o, a in opts:
			if o in ('-h, --help'):
				h = True
				print(hlp_txt)
				exit(0)
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
		main(port=prt, stn=stn, cha=cha, seconds=sec, spectrogram=spec, fullscreen=full
			 fullscreen=full)
	# except ValueError as e:
	# 	print('ERROR: %s' % e)
	# 	print(hlp_txt)
	# 	exit(2)
