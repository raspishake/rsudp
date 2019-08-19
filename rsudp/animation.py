import getopt, sys
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import math
from obspy import UTCDateTime
from datetime import datetime, timedelta
import rsudp.rs2obspy as rso
import threading
import queue


'''
A more complex example program that uses rs2obspy to build a stream, then
plots the result live until the user interrupts the program using CTRL+C.

Requires obspy, numpy, matplotlib, rs2obspy, and raspberryShake.
'''

# from https://docs.obspy.org/_modules/obspy/imaging/spectrogram.html#_nearest_pow_2:
def _nearest_pow_2(x):
	"""
	Find power of two nearest to x

	>>> _nearest_pow_2(3)
	2.0
	>>> _nearest_pow_2(15)
	16.0

	:type x: float
	:param x: Number
	:rtype: Int
	:return: Nearest power of 2 to x

	Adapted from the obspy library
	"""
	a = math.pow(2, math.ceil(np.log2(x)))
	b = math.pow(2, math.floor(np.log2(x)))
	if abs(a - x) < abs(b - x):
		return a
	else:
		return b


def live_stream(port=8888, sta='Z0000', cha='EHZ', seconds=30, spectrogram=False):
	'''
	Main function. Designed to run until user cancels with CTRL+C.
	This will attempt to live-plot a UDP stream from a Raspberry Shake device.
	'''
	width = 8								# plot width in inches
	bgcolor = '0.0'
	fgcolor = '0.8'
	linecolor = 'blue'

	mult = 1

	rso.init(port=port, sta=sta)			# initialize the port
	s = rso.init_stream()					# initialize a stream
	num_chans = len(rso.channels)			# number of channels sent to the port
	fig = plt.figure(figsize=(width,num_chans*3))

	fig.suptitle('Raspberry Shake station %s.%s live output' # title
					% (rso.RS.net, rso.RS.sta), fontsize=14)
	fig.patch.set_facecolor(bgcolor)		# background color
	ax = {}									# list for subplot axes

	q = queue.Queue()
	lock = threading.Lock()

	if spectrogram:							# things to set when spectrogram is True
		mult = 2
		per_lap = 0.9
		nfft1 = _nearest_pow_2(rso.sps)
		nlap1 = nfft1 * per_lap

	def slice_stream(s, seconds=seconds):
		obstart = s[0].stats.endtime - timedelta(seconds=seconds)	# obspy time
		start = np.datetime64(s[0].stats.endtime)-np.timedelta64(seconds, 's')	# numpy time
		end = np.datetime64(s[0].stats.endtime)	# numpy time
		return s.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)

	def data_listener(s=s):
		while True:
			lock.acquire()
			s = rso.update_stream(s, fill_value='latest')
			s = slice_stream(s)
			lock.release()

	def init():
		for line in lines:
			line.set_ydata([np.nan] * (seconds * rso.sps))
		return lines

	def update(frame):
		for t in s:
			lines[t.stats.channel].set_ydata(t.data)
		return lines


	try:
		thread = threading.Thread(target=data_listener)
		thread.daemon = True
		thread.start()
	

		ani = animation.FuncAnimation(
			fig, update, init_func=init, interval=1, blit=True, cache_frame_data=False)
		plt.show()

	except KeyboardInterrupt:
		print()
		rso.RS.printM('Plotting ended.')
		exit(0)

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
		prt, stn, sec = 8888, 'Z0000', 30
		h = False
		spec = False
		opts, args = getopt.getopt(sys.argv[1:], 'hp:s:n:d:c:g', ['help', 'port=', 'station=', 'duration=', 'channels=', 'spectrogram'])
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
		live_stream(port=prt, sta=stn, cha=cha, seconds=sec, spectrogram=spec)
	#	exit(0)
	# except ValueError as e:
	# 	print('ERROR: %s' % e)
	# 	print(hlp_txt)
	# 	exit(2)

if __name__ == '__main__':
	main()
