import sys, os
import getopt
import time
import rsudp.raspberryshake as RS
try:
	import matplotlib
	try:
		matplotlib.use('Qt5Agg')
	except:
		matplotlib.use('TkAgg')
	import matplotlib.pyplot as plt
	from matplotlib import animation
	plt.ion()
	mpl = True
except:
	mpl = False
	RS.printM('Could not import matplotlib, plotting will not be available')



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
	if outdir:
		writer = RS.WriteThread(outdir=outdir, stn=stn, debug=debug)
		writer.start()

	if plot and mpl:
		while True:
			if prod.numchns == 0:
				time.sleep(0.01)
				continue
			else:
				fig, ax, lines = setup_plot(num_chans=prod.numchns, seconds=sec,
											spectrogram=spec, sps=prod.sps,
											fullscreen=full)
				break
		plotter = RS.PlotThread(stn=stn, cha=cha, seconds=sec, spectrogram=spec,
							 	fullscreen=full)
		plotter.start()

		ani = animation.FuncAnimation(fig, animate, interval=250, fargs=(plotter.stream),
									  init_func=init_plot, blit=False,
									  repeat=False, cache_frame_data=False)


def setup_plot(num_chans, spectrogram, sps, seconds, fullscreen=False):
	"""
	Matplotlib is not threadsafe, so plots must be initialized outside of the thread.
	"""
	global fig, ax, lines
	bgcolor = '#202530' # background
	fgcolor = '0.8' # axis and label color
	linecolor = '#c28285' # seismogram color
	fig = plt.figure(figsize=(8,3))
	fig.patch.set_facecolor(bgcolor)		# background color
	fig.suptitle('Raspberry Shake station %s.%s live output' # title
				 % (RS.net, RS.stn), fontsize=14, color=fgcolor)
	ax, lines = [], []							# list for subplot axes
	mult = 1
	if fullscreen:
		figManager = plt.get_current_fig_manager()
		figManager.window.showMaximized()
	plt.draw()								# set up the canvas
	if spectrogram:
		mult = 2
		per_lap = 0.9
		nfft1 = _nearest_pow_2(rso.sps)
		nlap1 = nfft1 * per_lap
	for i in range(num_chans * mult):
		i += 1
		if i == 1:
			ax.append(fig.add_subplot(num_chans*mult, 1, i, label=str(i)))
			ax[i-1].set_facecolor(bgcolor)
			ax[i-1].tick_params(colors=fgcolor, labelcolor=fgcolor)
			if spectrogram:
				ax.append(fig.add_subplot(num_chans*mult, 1, i,
						  label=str(i)))#, sharex=ax[0]))
				ax[i-1].set_facecolor(bgcolor)
				ax[i-1].tick_params(colors=fgcolor, labelcolor=fgcolor)
		else:
			ax.append(fig.add_subplot(num_chans*mult, 1, i, sharex=ax[0],
					  label=str(i)))
			ax[i-1].set_facecolor(bgcolor)
			ax[i-1].tick_params(colors=fgcolor, labelcolor=fgcolor)
			if spectrogram:
				ax.append(fig.add_subplot(num_chans*mult, 1, i, sharex=ax[1],
						  label=str(i)))
				ax[i-1].set_facecolor(bgcolor)
				ax[i-1].tick_params(colors=fgcolor, labelcolor=fgcolor)
	for axis in ax:
		plt.setp(axis.spines.values(), color=fgcolor)
		plt.setp([axis.get_xticklines(), axis.get_yticklines()], color=fgcolor)
	for i in range(num_chans * mult):
		lines.append(ax[i*mult].plot([0,1], [0,1], color=fgcolor))
		ax[i*mult].set_ylabel('Voltage counts', color=fgcolor)
		if spectrogram:						# if the user wants a spectrogram, plot it
			if i == 0:
				sg = ax[1].specgram([0,1], NFFT=8, pad_to=8, Fs=sps, noverlap=7)[0]
				ax[1].set_xlim(0,seconds)
			ax[i*mult+1].set_ylim(0,int(sps/2))
	plt.draw()								# update the canvas
	fig.canvas.start_event_loop(0.001)		# wait (trust me this is necessary, but I don't know why)

	return fig, ax, lines

def init_plot():
	i = 0
	for line in lines:
		lines[i].set_ydata(np.ma.array(x, mask=True))
		i += 1
	return lines,

def animate(i, *fargs):
	i = 0
	for t in fargs[0]:
		lines[i].set_ydata(t.data)  # update the data
		i += 1
	return lines,



if __name__ == '__main__':
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
