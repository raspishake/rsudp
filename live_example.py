import getopt, sys
import rs2obspy as rso
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import math
from obspy import UTCDateTime
from datetime import datetime, timedelta

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
    """
    a = math.pow(2, math.ceil(np.log2(x)))
    b = math.pow(2, math.floor(np.log2(x)))
    if abs(a - x) < abs(b - x):
        return a
    else:
        return b

# from 
def time_ticks(x, pos):
    d = end.astype('O') - timedelta(seconds=sec) + timedelta(milliseconds=rso.sps)
    return str(d)

def live_stream(port=8888, sta='R4989', seconds=30, spectrogram=False):
	'''
	Main function. Designed to run until user cancels with CTRL+C,
	at which point it will create a simple trace plot.
	'''
	global sec, end
	sec = seconds

	rso.init(port=port, sta=sta)
	trate = rso.trate

	s = rso.init_stream()

	fig = plt.figure(figsize=(8,3*len(rso.channels)))
	fig.suptitle('Raspberry Shake station %s.%s live output'
				 % (rso.RS.net, rso.RS.sta), fontsize=14)
	fig.patch.set_facecolor('white')
	plt.draw()
	ax = []
	mult = 1
	if spectrogram:
		mult = 2
		per_lap = 0.9
		nfft1 = _nearest_pow_2(rso.sps)
		nlap1 = nfft1 * per_lap
	i = 1
	for c in rso.channels:
		if i == 1:
			ax.append(fig.add_subplot(len(rso.channels)*mult, 1, i))
			if spectrogram:
				i += 1
				ax.append(fig.add_subplot(len(rso.channels)*mult, 1, i))#, sharex=ax[0]))
		else:
			ax.append(fig.add_subplot(len(rso.channels)*mult, 1, i, sharex=ax[0]))
			if spectrogram:
				i += 1
				ax.append(fig.add_subplot(len(rso.channels)*mult, 1, i, sharex=ax[1]))
		s = rso.update_stream(s)
		i += 1
	plt.tight_layout(pad=3, h_pad=0, w_pad=0, rect=(0.03, 0, 1, 1))
	plt.draw()
	plt.pause(0.05)

	lines = []
	i = 0
	for t in s:
		start = np.datetime64(t.stats.endtime)-np.timedelta64(seconds, 's')
		end = np.datetime64(t.stats.endtime)
		r = np.arange(start,end,np.timedelta64(int(1000/rso.sps), 'ms'))[-len(t.data):]
		lines.append(ax[i*mult].plot(r, t.data, color='k',
					 lw=0.5, label=t.stats.channel)[0])
		ax[i*mult].set_ylabel('Voltage counts')
		ax[i*mult].legend(loc='upper left')
		if spectrogram:
			if i == 0:
				rso.RS.printM('Setting up spectrograms. Plots will update at most every 0.5 sec to reduce CPU load.')
				sg = ax[1].specgram(t.data, NFFT=8, pad_to=8, Fs=rso.sps, noverlap=7)[0]
				ax[1].set_xlim(0,seconds)
			ax[i*mult+1].set_ylim(0,int(rso.sps/2))
		i += 1
	ax[i*mult-1].set_xlabel('Time (UTC)')
	rso.RS.printM('Plot set up successfully. Will run until CTRL+C keystroke.')

	try:
		while True:
			i = 0
			while i < len(rso.channels)*mult*(rso.sps/100):					# way of reducing CPU load while keeping stream up to date
				s = rso.update_stream(s)
				i += 1
			obstart = s[0].stats.endtime - timedelta(seconds=seconds)
			start = np.datetime64(s[0].stats.endtime)-np.timedelta64(seconds, 's')
			end = np.datetime64(s[0].stats.endtime)
			s = s.slice(starttime=obstart)
			i = 0
			while i < len(rso.channels):
				r = np.arange(start, end, np.timedelta64(int(1000/rso.sps), 'ms'))[-len(s[i].data[-rso.sps*seconds:]):]
				lines[i].set_ydata(s[i].data[-rso.sps*seconds:])
				lines[i].set_xdata(r)
				ax[i*mult].set_xlim(left=start, right=end)
				ax[i*mult].set_ylim(bottom=np.min(s[i].data)-np.ptp(s[i].data)*0.1, top=np.max(s[i].data)+np.ptp(s[i].data)*0.1)
				if spectrogram:
					nfft1 = _nearest_pow_2(rso.sps)
					nlap1 = nfft1 * per_lap
					if len(s[i].data) < nfft1:
						nfft1 = 8
						nlap1 = 6
					sg = ax[i*mult+1].specgram(s[i].data, NFFT=nfft1, pad_to=int(rso.sps*2), Fs=rso.sps, noverlap=nlap1)[0]
					ax[i*mult+1].clear()
					ax[i*mult+1].set_xlim(0,seconds)
					ax[i*mult+1].set_ylim(0,int(rso.sps/2))
					ax[i*mult+1].imshow(np.flipud(sg**(1/10)), extent=(seconds-(1/(rso.sps/len(s[i].data))),seconds,0,rso.sps/2), aspect='auto')
					ax[i*mult+1].tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
					ax[i*mult+1].set_ylabel('Frequency (Hz)')
				i += 1
			ax[i*mult-1].set_xlabel('Time (UTC)')
			plt.pause(0.01)
	except KeyboardInterrupt:
		print()
		rso.RS.printM('Plotting ended.')
		exit(0)
	except Exception as e:
		print()
		rso.RS.printM('ERROR: %s' % e)
		exit(2)


if __name__ == '__main__':
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

	try:
		prt, stn, sec = 8888, 'Z0000', 30
		h = False
		opts, args = getopt.getopt(sys.argv[1:], 'hp:s:n:d:', ['help', 'port=', 'station=', 'duration='])
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
		live_stream(port=prt, sta=stn, seconds=sec)
		exit(0)
	except Exception as e:
		if not h:
			print('ERROR: %s' % e)
			print(hlp_txt)
			exit(2)
		else:
			exit(0)
