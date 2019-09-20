import os, sys
from threading import Thread
from queue import Queue
import time
import math
import numpy as np
from datetime import datetime, timedelta
import rsudp.raspberryshake as RS
from rsudp.raspberryshake import qsize
from rsudp.consumer import destinations
from rsudp import printM
import linecache
sender = 'plot.py'
try:		# test for matplotlib and exit if import fails
	import matplotlib
	if 'armv' in os.uname().machine:	# test for Qt and fail over to Tk
		printM('WARNING: Running on %s architecture, using Tk instead of Qt' % (os.uname().machine), sender)
		matplotlib.use('TkAgg')
		qt = False
	else:
		matplotlib.use('Qt5Agg')
		qt = True
	import matplotlib.pyplot as plt
	plt.ion()
	mpl = True
except:
	mpl = False
	printM('ERROR: Could not import matplotlib, plotting will not be available.', sender)
	printM('       Thread exiting.', sender)
	sys.stdout.flush()
	sys.exit()


class Plot(Thread):
	def __init__(self, cha='all',
				 seconds=30, spectrogram=False,
				 fullscreen=False, qt=qt):
		"""
		Initialize the plot process


		"""
		super().__init__()
		global destinations

		plotq = Queue(qsize)
		destinations.append(plotq)
		self.sender = 'Plot'
		printM('Starting.', self.sender)

		self.qno = len(destinations) - 1
		self.stream = RS.Stream()
		self.stn = RS.stn
		self.net = RS.net
		self.chans = []
		cha = RS.chns if (cha == 'all') else cha
		cha = list(cha) if isinstance(cha, str) else cha
		l = RS.chns
		for c in l:
			n = 0
			for uch in cha:
				if (uch.upper() in c) and (c not in str(self.chans)):
					self.chans.append(c)
				n += 1
		if len(self.chans) < 1:
			self.chans = RS.chns
		printM('Plotting channels: %s' % self.chans, self.sender)
		self.totchns = RS.numchns
		self.seconds = seconds
		self.spectrogram = spectrogram
		self.per_lap = 0.9
		self.fullscreen = fullscreen
		self.qt = qt
		self.num_chans = len(self.chans)
		self.delay = 2 if (self.num_chans > 1) and (self.spectrogram) else 1
		# plot stuff
		self.bgcolor = '#202530' # background
		self.fgcolor = '0.8' # axis and label color
		self.linecolor = '#c28285' # seismogram color

	def getq(self):
		d = destinations[self.qno].get()
		destinations[self.qno].task_done()
		if 'TERM' in str(d):
			plt.close()
			sys.exit()
		if RS.getCHN(d) in self.chans:
			self.stream = RS.update_stream(
				stream=self.stream, d=d, fill_value='latest')
			return True
		else:
			return False
		
	def set_sps(self):
		self.sps = RS.sps

	# from https://docs.obspy.org/_modules/obspy/imaging/spectrogram.html#_nearest_pow_2:
	def _nearest_pow_2(self, x):
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

	def setup_plot(self):
		"""
		Matplotlib is not threadsafe, so things are a little weird here.
		"""
		# instantiate a figure and set basic params
		self.fig = plt.figure(figsize=(8,3*self.num_chans))
		self.fig.patch.set_facecolor(self.bgcolor)	# background color
		self.fig.suptitle('Raspberry Shake station %s.%s live output' # title
					% (self.net, self.stn), fontsize=14, color=self.fgcolor)
		self.ax, self.lines = [], []				# list for subplot axes and lines artists
		self.mult = 1					# spectrogram selection multiplier
		if self.spectrogram:
			self.mult = 2				# 2 if user wants a spectrogram else 1
			if self.seconds > 60:
				self.per_lap = 0.9		# if axis is long, spectrogram overlap can be shorter
			else:
				self.per_lap = 0.975	# if axis is short, increase resolution
			# set spectrogram parameters
			self.nfft1 = self._nearest_pow_2(self.sps)
			self.nlap1 = self.nfft1 * self.per_lap

		for i in range(self.num_chans):
			if i == 0:
				# set up first axes (axes added later will share these x axis limits)
				self.ax.append(self.fig.add_subplot(self.num_chans*self.mult,
							   1, 1, label=str(1)))
				self.ax[0].set_facecolor(self.bgcolor)
				self.ax[0].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)
				if self.spectrogram:
					self.ax.append(self.fig.add_subplot(self.num_chans*self.mult,
								   1, 2, label=str(2)))#, sharex=ax[0]))
					self.ax[1].set_facecolor(self.bgcolor)
					self.ax[1].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)
			else:
				# add axes that share either lines or spectrogram axis limits
				s = i * self.mult	# plot selector
				# add a subplot then set colors
				self.ax.append(self.fig.add_subplot(self.num_chans*self.mult,
							   1, s+1, sharex=self.ax[0], label=str(s+1)))
				self.ax[s].set_facecolor(self.bgcolor)
				self.ax[s].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)
				if self.spectrogram:
					# add a spectrogram and set colors
					self.ax.append(self.fig.add_subplot(self.num_chans*self.mult,
								   1, s+2, sharex=self.ax[1], label=str(s+2)))
					self.ax[s+1].set_facecolor(self.bgcolor)
					self.ax[s+1].tick_params(colors=self.fgcolor, labelcolor=self.fgcolor)

		for axis in self.ax:
			# set the rest of plot colors
			plt.setp(axis.spines.values(), color=self.fgcolor)
			plt.setp([axis.get_xticklines(), axis.get_yticklines()], color=self.fgcolor)

		# calculate times
		start = np.datetime64(self.stream[0].stats.endtime
							  )-np.timedelta64(self.seconds, 's')	# numpy time
		end = np.datetime64(self.stream[0].stats.endtime)	# numpy time

		# set up axes and artists
		for i in range(self.num_chans): # create lines objects and modify axes
			if len(self.stream[i].data) < int(self.sps*(1/self.per_lap)):
				comp = 0				# spectrogram offset compensation factor
			else:
				comp = 1/self.per_lap	# spectrogram offset compensation factor
			r = np.arange(start, end, np.timedelta64(int(1000/self.sps), 'ms'))[-len(
						  self.stream[i].data[int(-self.sps*(self.seconds-(comp/2))):-int(self.sps*(comp/2))]):]
			mean = int(round(np.mean(self.stream[i].data)))
			# add artist to lines list
			self.lines.append(self.ax[i*self.mult].plot(r,
							  np.nan*(np.zeros(len(r))),
							  label=self.stream[i].stats.channel, color=self.linecolor,
							  lw=0.45)[0])
			# set axis limits
			self.ax[i*self.mult].set_xlim(left=start.astype(datetime),
										  right=end.astype(datetime))
			self.ax[i*self.mult].set_ylim(bottom=np.min(self.stream[i].data-mean)
										  -np.ptp(self.stream[i].data-mean)*0.1,
										  top=np.max(self.stream[i].data-mean)
										  +np.ptp(self.stream[i].data-mean)*0.1)
			# we can set line plot labels here, but not imshow labels
			self.ax[i*self.mult].set_ylabel('Voltage counts', color=self.fgcolor)
			self.ax[i*self.mult].legend(loc='upper left')	# legend and location
			if self.spectrogram:		# if the user wants a spectrogram, plot it
				# add spectrogram to axes list
				sg = self.ax[1].specgram(self.stream[i].data, NFFT=8, pad_to=8,
										 Fs=self.sps, noverlap=7, cmap='inferno',
										 xextent=(self.seconds-0.5, self.seconds))[0]
				self.ax[1].set_xlim(0,self.seconds)
				self.ax[i*self.mult+1].set_ylim(0,int(self.sps/2))
				self.ax[i*self.mult+1].imshow(np.flipud(sg**(1/float(10))), cmap='inferno',
						extent=(self.seconds-(1/(self.sps/float(len(self.stream[i].data)))),
								self.seconds,0,self.sps/2), aspect='auto')

		# update canvas and draw
		if self.fullscreen: # set up fullscreen
			figManager = plt.get_current_fig_manager()
			if self.qt:	# try maximizing in Qt first
				figManager.window.showMaximized()
			else:	# if Qt fails, try Tk
				figManager.resize(*figManager.window.maxsize())

		plt.draw()									# draw the canvas
		self.fig.canvas.start_event_loop(0.005)		# wait for canvas to update
		if self.fullscreen:		# carefully designed plot layout parameters
			plt.tight_layout(pad=0, rect=[0.015, 0.01, 0.99, 0.955])	# [left, bottom, right, top]
		else:	# carefully designed plot layout parameters
			plt.tight_layout(pad=0, h_pad=0.1, w_pad=0,
							 rect=[0.015, 0.01, 0.99, 0.885+(0.02*self.num_chans)])	# [left, bottom, right, top]

	def update_plot(self):
		obstart = self.stream[0].stats.endtime - timedelta(seconds=self.seconds)	# obspy time
		start = np.datetime64(self.stream[0].stats.endtime
							  )-np.timedelta64(self.seconds, 's')	# numpy time
		end = np.datetime64(self.stream[0].stats.endtime)	# numpy time
		self.stream = self.stream.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)
		i = 0
		for i in range(self.num_chans):	# for each channel, update the plots
			comp = 1/self.per_lap	# spectrogram offset compensation factor
			r = np.arange(start, end, np.timedelta64(int(1000/self.sps), 'ms'))[-len(
						self.stream[i].data[int(-self.sps*(self.seconds-(comp/2))):-int(self.sps*(comp/2))]):]
			mean = int(round(np.mean(self.stream[i].data)))
			self.lines[i].set_ydata(self.stream[i].data[int(-self.sps*(self.seconds-(comp/2))):-int(self.sps*(comp/2))]-mean)
			self.lines[i].set_xdata(r)	# (1/self.per_lap)/2
			self.ax[i*self.mult].set_xlim(left=start.astype(datetime)+timedelta(seconds=comp*1.5),
										  right=end.astype(datetime))
			self.ax[i*self.mult].set_ylim(bottom=np.min(self.stream[i].data-mean)
										  -np.ptp(self.stream[i].data-mean)*0.1,
										  top=np.max(self.stream[i].data-mean)
										  +np.ptp(self.stream[i].data-mean)*0.1)
			if self.spectrogram:
				self.nfft1 = self._nearest_pow_2(self.sps)	# FFTs run much faster if the number of transforms is a power of 2
				self.nlap1 = self.nfft1 * self.per_lap
				if len(self.stream[i].data) < self.nfft1:	# when the number of data points is low, we just need to kind of fake it for a few fractions of a second
					self.nfft1 = 8
					self.nlap1 = 6
				sg = self.ax[i*self.mult+1].specgram(self.stream[i].data-mean,
							NFFT=self.nfft1, pad_to=int(self.sps*4),
							Fs=self.sps, noverlap=self.nlap1)[0]	# meat & potatoes
				self.ax[i*self.mult+1].clear()	# incredibly important, otherwise continues to draw over old images (gets exponentially slower)
				# cloogy way to shift the spectrogram to line up with the seismogram
				self.ax[i*self.mult+1].set_xlim(0.25,self.seconds-0.25)
				self.ax[i*self.mult+1].set_ylim(0,int(self.sps/2))
				# imshow to update the spectrogram
				self.ax[i*self.mult+1].imshow(np.flipud(sg**(1/float(10))), cmap='inferno',
						extent=(self.seconds-(1/(self.sps/float(len(self.stream[i].data)))),
								self.seconds,0,self.sps/2), aspect='auto')
				# some things that unfortunately can't be in the setup function:
				self.ax[i*self.mult+1].tick_params(axis='x', which='both',
						bottom=False, top=False, labelbottom=False)
				self.ax[i*self.mult+1].set_ylabel('Frequency (Hz)', color=self.fgcolor)
				self.ax[i*self.mult+1].set_xlabel('Time (UTC)', color=self.fgcolor)
			else:
				# also can't be in the setup function
				self.ax[i*self.mult].set_xlabel('Time (UTC)', color=self.fgcolor)

	def loop(self):
		"""
		Let some time elapse in order for the plot canvas to draw properly.
		Must be separate from :func:`update_plot()` to avoid a broadcast error early in plotting.
		Takes no arguments except :py:code:`self`.
		"""
		self.fig.canvas.start_event_loop(0.005)

	def run(self):
		"""
		The heart of the plotting routine.

		Begins by updating the queue to populate a :py:`obspy.core.stream.Stream` object, then setting up the main plot.
		The first time through the main loop, the plot is not drawn. After that, the plot is drawn every time all channels are updated.
		Any plots containing a spectrogram and more than 1 channel are drawn at most every half second (500 ms).
		All other plots are drawn at most every quarter second (250 ms).
		"""
		self.getq() # block until data is flowing from the consumer
		for i in range((self.totchns)*2): # fill up a stream object
			self.getq()
		self.set_sps()

		self.setup_plot()
		i = 0	# number of plot events
		u = -1	# number of queue calls
		while True: # main loop
			while True:
				if destinations[self.qno].qsize() > 0:
					self.getq()
					time.sleep(0.009)		# wait a ms to see if another packet will arrive
				else:
					u += 1 if self.getq() else 0
					if int(u/(self.num_chans*self.delay)) == float(u/(self.num_chans*self.delay)):
						break

			if i > 10:
				linecache.clearcache()
				i = 0
			else:
				i += 1
			self.stream = RS.copy(self.stream)
			self.update_plot()
			if u >= 0:				# avoiding a matplotlib broadcast error
				self.loop()

			u = 0
			time.sleep(0.005)		# wait a ms to see if another packet will arrive
			sys.stdout.flush()