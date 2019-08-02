import getopt, sys
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import numpy as np
import math
from obspy import UTCDateTime
from datetime import datetime, timedelta
import rsh_udp.rs2obspy as rso
import gc

plt.ion()


####################################################
####################################################
import linecache
import os
import tracemalloc

def display_top(snapshot, key_type='lineno', limit=10):
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)

    print("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace "/path/to/module/file.py" with "module/file.py"
        filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        print("#%s: %s:%s: %.1f KiB"
              % (index, filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    print("Total allocated size: %.1f KiB" % (total / 1024))

tracemalloc.start()
####################################################
####################################################

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
	plt.pause(0.05)							# wait (trust me this is necessary, but I don't know why)

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

	rso.init(port=port, sta=sta)			# initialize the port
	s = rso.init_stream()					# initialize a stream
	num_chans = len(rso.channels)

	if spectrogram:
		rso.RS.printM('Spectrogram is enabled; plots will update at most every 0.5 sec to reduce CPU load.')
		s, fig, ax, lines, mult, sg, per_lap, nfft1, nlap1 = plot_gen(
				s, figsize=(width,3*num_chans), seconds=seconds, spectrogram=spectrogram
			)	# set up plot with spectrograms
		regen_mult = 1	# low regeneration time (FFTs eat up lots of resources)
	else:
		s, fig, ax, lines, mult = plot_gen(s, figsize=(width,3*num_chans), seconds=seconds)	# standard waveform plotting
		regen_mult = 2	# higher regeneration time
	rso.RS.printM('Plot set up successfully. Will run until CTRL+C keystroke.')

	try:
		n = 1
		regen_denom = 900.*float(regen_mult)
		while True:		# main loop
			regen_time = ((float(n)*num_chans) / regen_denom)		# calculate if 900*regen_mult iterations have passed
			if regen_time == int(regen_time):						# purge mpl memory objects and regenerate plot
				if n > 1:
					width = fig.get_size_inches()[0]				# get the current figure width (inches)
					plt.close('all')								# close all matplotlib objects
					gc.collect()									# clean up garbage
					plt.ion()
				if spectrogram:
					s, fig, ax, lines, mult, sg, per_lap, nfft1, nlap1 = plot_gen(
							s, figsize=(width,3*num_chans), seconds=seconds, spectrogram=spectrogram
						)	# regenerate all plots
				else:
					s, fig, ax, lines, mult = plot_gen(s, figsize=(width,3*num_chans), seconds=seconds)	# regenerate line plot
				if n > 1:
					rso.RS.printM('Plot regenerated after %s loops.' % (n))
					snapshot = tracemalloc.take_snapshot()
					display_top(snapshot)

			i = 0
			while i < num_chans*mult*(float(rso.sps)/100):	# way of reducing CPU load while keeping stream up to date
				s = rso.update_stream(s, fill_value='latest')	# this will update twice per channel if spectrogram==True and sps==100, otherwise once
				i += 1
			obstart = s[0].stats.endtime - timedelta(seconds=seconds)	# obspy time
			start = np.datetime64(s[0].stats.endtime)-np.timedelta64(seconds, 's')	# numpy time
			end = np.datetime64(s[0].stats.endtime)	# numpy time
			s = s.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)
			i = 0
			while i < num_chans:	# for each channel, update the plots
				r = np.arange(start, end, np.timedelta64(int(1000/rso.sps), 'ms'))[-len(s[i].data[-rso.sps*seconds:]):]
				lines[i].set_ydata(s[i].data[-rso.sps*seconds:])
				lines[i].set_xdata(r)
				ax[i*mult].set_xlim(left=start.astype(datetime), right=end.astype(datetime))
				ax[i*mult].set_ylim(bottom=np.min(s[i].data)-np.ptp(s[i].data)*0.1, top=np.max(s[i].data)+np.ptp(s[i].data)*0.1)
				if spectrogram:
					nfft1 = _nearest_pow_2(rso.sps)	# FFTs run much faster if the number of transforms is a power of 2
					nlap1 = nfft1 * per_lap
					if len(s[i].data) < nfft1:	# when the number of data points is low, we just need to kind of fake it for a few fractions of a second
						nfft1 = 8
						nlap1 = 6
					sg = ax[i*mult+1].specgram(s[i].data, NFFT=nfft1, pad_to=int(rso.sps*2),
							Fs=rso.sps, noverlap=nlap1)[0]	# meat & potatoes
					ax[i*mult+1].clear()	# incredibly important, otherwise continues to draw over old images (gets exponentially slower)
					ax[i*mult+1].set_xlim(0,seconds)
					ax[i*mult+1].set_ylim(0,int(rso.sps/2))
					ax[i*mult+1].imshow(np.flipud(sg**(1/float(10))),
							extent=(seconds-(1/(rso.sps/float(len(s[i].data)))),seconds,0,rso.sps/2), aspect='auto'
						)
					ax[i*mult+1].tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
					ax[i*mult+1].set_ylabel('Frequency (Hz)')
				i += 1
			ax[i*mult-1].set_xlabel('Time (UTC)')
			plt.pause(0.01)	# let the dust settle
			n += 1		# total iterations

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
