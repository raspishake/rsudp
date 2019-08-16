import getopt, sys
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import linecache
import numpy as np
import math
from obspy import UTCDateTime
from datetime import datetime, timedelta
import rsudp.rs2obspy as rso
import gc

plt.ion()


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

def plot_gen(s, figsize=(8,3), seconds=30, spectrogram=False):
	"""
	Generate a new plot on command with a stream object.
	"""
	fig = plt.figure(figsize=figsize)	# create a figure
	fig.suptitle('Raspberry Shake station %s.%s live output' # title
				 % (rso.RS.net, rso.RS.sta), fontsize=14)
	fig.patch.set_facecolor('white')		# background color
	plt.draw()								# set up the canvas
	ax = []									# list for subplot axes
	mult = 1
	num_chans = len(rso.channels)
	if spectrogram:							# things to set when spectrogram is True
		mult = 2
		per_lap = 0.9
		nfft1 = _nearest_pow_2(rso.sps)
		nlap1 = nfft1 * per_lap
	i = 1
	for c in rso.channels:					# for each channel, add a plot; if spectrogram==True, add another plot
		if i == 1:
			ax.append(fig.add_subplot(num_chans*mult, 1, i))
			if spectrogram:
				i += 1
				ax.append(fig.add_subplot(num_chans*mult, 1, i))#, sharex=ax[0]))
		else:
			ax.append(fig.add_subplot(num_chans*mult, 1, i, sharex=ax[0]))
			if spectrogram:
				i += 1
				ax.append(fig.add_subplot(num_chans*mult, 1, i, sharex=ax[1]))
		s = rso.update_stream(s)
		i += 1

		obstart = s[0].stats.endtime - timedelta(seconds=seconds)	# obspy time
		start = np.datetime64(s[0].stats.endtime)-np.timedelta64(seconds, 's')	# numpy time
		end = np.datetime64(s[0].stats.endtime)	# numpy time
		s = s.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)

	plt.tight_layout(pad=3, h_pad=0, w_pad=0, rect=(0.03, 0, 1, 1))	# carefully designed plot layout parameters
	plt.draw()								# update the canvas
	plt.pause(0.01)							# wait (trust me this is necessary, but I don't know why)

	lines = []								# lines objects to update
	i = 0
	for t in s:								# for trace in stream
		start = np.datetime64(t.stats.endtime)-np.timedelta64(seconds, 's')
		end = np.datetime64(t.stats.endtime)
		r = np.arange(start,end,np.timedelta64(int(1000/rso.sps), 'ms')).astype(datetime)[-len(t.data):] # array range of times in trace
		lines.append(ax[i*mult].plot(r, t.data[:(seconds*rso.sps)], color='k',
					 lw=0.5, label=t.stats.channel)[0])	# plot the line on the axis and put the instance in a list
		ax[i*mult].set_ylabel('Voltage counts')
		ax[i*mult].legend(loc='upper left')
		if spectrogram:						# if the user wants a spectrogram, plot it
			if i == 0:
				sg = ax[1].specgram(t.data, NFFT=8, pad_to=8, Fs=rso.sps, noverlap=7)[0]
				ax[1].set_xlim(0,seconds)
			ax[i*mult+1].set_ylim(0,int(rso.sps/2))
		i += 1
	ax[i*mult-1].set_xlabel('Time (UTC)')

	if spectrogram:
		return s, fig, ax, lines, mult, sg, per_lap, nfft1, nlap1
	else:
		return s, fig, ax, lines, mult
	

def live_stream(port=8888, sta='Z0000', seconds=30, spectrogram=False):
	'''
	Main function. Designed to run until user cancels with CTRL+C.
	This will attempt to live-plot a UDP stream from a Raspberry Shake device.
	'''
	width = 8								# plot width in inches
	mult = 1

	rso.init(port=port, sta=sta)			# initialize the port
	s = rso.init_stream()					# initialize a stream

	num_chans = len(rso.channels)
	fig, ax = plt.subplots(figsize=(width,num_chans*3))

	fig.suptitle('Raspberry Shake station %s.%s live output' # title
					% (rso.RS.net, rso.RS.sta), fontsize=14)
	fig.patch.set_facecolor('white')		# background color
	ax = []									# list for subplot axes
	if spectrogram:							# things to set when spectrogram is True
		mult = 2
		per_lap = 0.9
		nfft1 = _nearest_pow_2(rso.sps)
		nlap1 = nfft1 * per_lap

	def slice_stream(s):
		obstart = s[0].stats.endtime - timedelta(seconds=seconds)	# obspy time
		start = np.datetime64(s[0].stats.endtime)-np.timedelta64(seconds, 's')	# numpy time
		end = np.datetime64(s[0].stats.endtime)	# numpy time
		return s.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)

	i = 1
	for c in rso.channels:					# for each channel, add a plot; if spectrogram==True, add another plot
		if i == 1:
			ax.append(fig.add_subplot(num_chans*mult, 1, i))
			if spectrogram:
				i += 1
				ax.append(fig.add_subplot(num_chans*mult, 1, i))#, sharex=ax[0]))
		else:
			ax.append(fig.add_subplot(num_chans*mult, 1, i, sharex=ax[0]))
			if spectrogram:
				i += 1
				ax.append(fig.add_subplot(num_chans*mult, 1, i, sharex=ax[1]))
		s = rso.update_stream(s)
		i += 1	
		s = slice_stream(s)


	lines = []								# lines objects to update

	i = 0
	for t in s:								# for trace in stream
		start = np.datetime64(t.stats.endtime)-np.timedelta64(seconds, 's')
		end = np.datetime64(t.stats.endtime)
		r = np.arange(start,end,np.timedelta64(int(1000/rso.sps), 'ms')).astype(datetime)[-len(t.data):] # array range of times in trace
		lines.append(ax[i*mult].plot(r, t.data[:(seconds*rso.sps)], color='k',
					 lw=0.5, label=t.stats.channel)[0])	# plot the line on the axis and put the instance in a list
		ax[i*mult].set_ylabel('Voltage counts')
		ax[i*mult].legend(loc='upper left')
		if spectrogram:						# if the user wants a spectrogram, plot it
			if i == 0:
				sg = ax[1].specgram(t.data, NFFT=8, pad_to=8, Fs=rso.sps, noverlap=7)[0]
				ax[1].set_xlim(0,seconds)
			ax[i*mult+1].set_ylim(0,int(rso.sps/2))
		i += 1
	ax[i*mult-1].set_xlabel('Time (UTC)')

	def init():
		for line in lines:
			line.set_ydata([np.nan] * (seconds * rso.sps))
	def update():
		i = 0
		while i < num_chans*mult*(float(rso.sps)/100):	# way of reducing CPU load while keeping stream up to date
			s = rso.update_stream(s, fill_value='latest')	# this will update twice per channel if spectrogram==True and sps==100, otherwise once
			i += 1
		s = slice_stream(s)
		i = 0
		for t in s:
			lines[i].set_ydata(t.data)


	try:
		ani = animation.FuncAnimation(
			fig, update, init_func=init, interval=2, blit=True, save_count=50)
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
		opts, args = getopt.getopt(sys.argv[1:], 'hp:s:n:d:g', ['help', 'port=', 'station=', 'duration=', 'spectrogram'])
		for o, a in opts:
			if o in ('-h, --help'):
				h = True
				print(hlp_txt)
				exit(0)
			if o in ('-p', 'port='):
				prt = int(a)
			if o in ('-s', 'station='):
				stn = str(a)
			if o in ('-d', 'duration='):
				sec = int(a)
			if o in ('-g', '--spectrogram'):
				spec = True
		live_stream(port=prt, sta=stn, seconds=sec, spectrogram=spec)
	#	exit(0)
	# except ValueError as e:
	# 	print('ERROR: %s' % e)
	# 	print(hlp_txt)
	# 	exit(2)

if __name__ == '__main__':
	main()
