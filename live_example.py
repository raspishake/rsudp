import getopt, sys
import rs2obspy as rso
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from obspy import UTCDateTime
from datetime import datetime, timedelta
import time

matplotlib.use('Qt4Agg')
plt.ion()

'''
A small example program that uses rs2obspy to build a stream, then
plots the result when the user interrupts the program using CTRL+C.

Requires obspy, numpy, rs2obspy, and raspberryShake.
'''

def live_stream(port=8888, sta='R4989', seconds=30, net='AM'):
	'''
	Main function. Designed to run until user cancels with CTRL+C,
	at which point it will create a simple trace plot.
	'''
	rso.init(port=port, sta=sta, net=net)

	s = rso.init_stream()

	fig = plt.figure(figsize=(8,8))
	fig.suptitle('Raspberry Shake station %s.%s live output'
				 % (rso.network, rso.station), fontsize=14)
	fig.patch.set_facecolor('white')
	plt.draw()
	ax = []
	i = 1
	for c in rso.channels:
		if i == 1:
			ax.append(fig.add_subplot(len(rso.channels), 1, i))
		else:
			ax.append(fig.add_subplot(len(rso.channels), 1, i, sharex=ax[0]))
		s = rso.update_stream(s)
		i += 1
	plt.draw()
	plt.pause(0.05)

	lines = []
	i = 0
	for t in s:
		start = np.datetime64(t.stats.endtime)-np.timedelta64(seconds, 's')
		end = np.datetime64(t.stats.endtime)
		r = np.arange(start,end,np.timedelta64(int(1000/rso.sps), 'ms'))[-len(t.data):]
		lines.append(ax[i].plot(r, t.data, color='k',
					 lw=0.5, label=t.stats.channel)[0])
		ax[i].set_ylabel('Voltage counts')
		ax[i].legend(loc='upper left')
		i += 1
	ax[i-1].set_xlabel('Time (UTC)')


	try:
		while True:
			i = 0
			s = rso.update_stream(s)
			obstart = t.stats.endtime - timedelta(seconds=seconds)
			start = np.datetime64(t.stats.endtime)-np.timedelta64(seconds, 's')
			end = np.datetime64(t.stats.endtime)
			trate = rso.trate + 0
			s = s.slice(starttime=obstart+timedelta(milliseconds=trate))
			for t in s:
				r = np.arange(start,end,np.timedelta64(int(1000/rso.sps), 'ms'))[-len(t.data):]
				lines[i].set_ydata(t.data)
				lines[i].set_xdata(r)
				ax[i].set_xlim(left=start, right=end)
				ax[i].set_ylim(bottom=np.min(t.data)-abs(np.min(t.data))*0.1, top=np.max(t.data)+abs(np.max(t.data))*0.1)
				i += 1
			plt.pause(0.01)
	except KeyboardInterrupt:
		time.sleep(0.1)

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
## Loads port, station, network, and duration arguments to create a graph.  ##
## Supply -p, -s, -n, and/or -d to change the port and the output plot      ##
## parameters.                                                              ##
##                                                                          ##
## Requires:                                                                ##
## - Numpy                                                                  ##
## - ObsPy                                                                  ##
## - Matplotlib                                                             ##
## - rs2obspy                                                               ##
## - raspberryShake                                                         ##
##                                                                          ##
## The following example sets the port to 18002, station to R0E05,          ##
## network to AM, and plot duration to 25 seconds, then plots data live:    ##
##                                                                          ##
##############################################################################
##                                                                          ##
##    $ python live_example.py -p 18001 -s R0E05 -n AM -d 25                ##
##                                                                          ##
##############################################################################

	'''

	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hp:s:n:d:', ['help=', 'port=', 'station=', 'network=', 'duration='])
		prt, stn, nw, sec = None, None, None, None
		h = False
		for o, a in opts:
			if o in ('-h, --help'):
				h = True
				print(hlp_txt)
				exit(0)
			if o in ('-p', '--port', '--port='):
				prt = int(a)
			if o in ('-s', '--station', '--station='):
				stn = str(a)
			if o in ('-n', '--network', '--network='):
				nw = str(a)
			if o in ('-d', '--duration', '--duration='):
				sec = int(a)
		live_stream(port=prt, sta=stn, net=nw, seconds=sec)
	except Exception as e:
		if not h:
			print('ERROR: %s' % e)
			print(hlp_txt)
			exit(2)
		else:
			exit(0)
