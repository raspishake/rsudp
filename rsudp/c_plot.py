import os, sys
import pkg_resources as pr
from threading import Thread
import time
import math
import numpy as np
from datetime import datetime, timedelta
import rsudp.raspberryshake as RS
from rsudp import printM
import rsudp
import linecache
sender = 'plot.py'
try:		# test for matplotlib and exit if import fails
	from matplotlib import use
	if 'armv' in os.uname().machine:	# test for Qt and fail over to Tk
		use('TkAgg')
		from tkinter import PhotoImage
		qt = False
	else:
		use('Qt5Agg')
		from PyQt5 import QtGui
		qt = True
	import matplotlib.pyplot as plt
	import matplotlib.dates as mdates
	import matplotlib.image as mpimg
	plt.ion()
	mpl = True
	import warnings
	warnings.filterwarnings("ignore", module="matplotlib")
except:
	printM('[Plot] ERROR: Could not import matplotlib, plotting will not be available.', sender)
	printM('[Plot]        Thread will exit now.', sender)
	mpl = False

icon = 'icon.ico'
icon2 = 'icon.png'

class Plot(Thread):
	def __init__(self, cha='all', q=False,
				 seconds=30, spectrogram=False,
				 fullscreen=False, qt=qt, deconv=False,
				 screencap=False, alert=False):
		"""
		Initialize the plot process


		"""
		super().__init__()
		self.sender = 'Plot'
		self.alive = True
		self.alarm = False

		if mpl == False:
			sys.stdout.flush()
			sys.exit()
		if qt == False:
			printM('WARNING: Running on %s architecture, using Tk instead of Qt' % (os.uname().machine), self.sender)
		if q:
			self.queue = q
		else:
			printM('ERROR: no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			sys.exit()

		printM('Starting.', self.sender)

		self.stream = RS.Stream()
		self.raw = RS.Stream()
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

		self.deconv = deconv if (deconv == 'ACC') or (deconv == 'VEL') or (deconv == 'DISP') else False
		if self.deconv and RS.inv:
			deconv = deconv.upper()
			self.units = 'Acceleration (m$^2$/s)' if (self.deconv == 'ACC') else False
			self.units = 'Velocity (m/s)' if (self.deconv == 'VEL') else self.units
			self.units = 'Displacement (m)' if (self.deconv == 'DISP') else self.units
			printM('Signal deconvolution set to %s' % (self.deconv), self.sender)
		else:
			self.units = 'Voltage counts'
			self.deconv = False
		printM('Seismogram units are %s' % (self.units), self.sender)

		self.per_lap = 0.9
		self.fullscreen = fullscreen
		self.qt = qt
		self.num_chans = len(self.chans)
		self.delay = RS.tr if (self.spectrogram) else 1

		self.screencap = screencap
		self.save = False
		self.save_timer = 0
		self.events = 0
		self.event_text = ' - detected events: 0' if alert else ''
		self.last_event = False
		# plot stuff
		self.bgcolor = '#202530' # background
		self.fgcolor = '0.8' # axis and label color
		self.linecolor = '#c28285' # seismogram color
		self.figimage = False

	def deconvolve(self):
		self.stream = self.raw.copy()
		for trace in self.stream:
			trace.stats.units = self.units
			if self.deconv:
				if ('HZ' in trace.stats.channel) or ('HE' in trace.stats.channel) or ('HN' in trace.stats.channel):
					trace.remove_response(inventory=RS.inv, pre_filt=[0.1, 0.6, 0.95*self.sps, self.sps],
											output=self.deconv, water_level=4.5, taper=False)
					if 'ACC' in self.deconv:
						trace.data = np.gradient(trace.data, 1)
					elif 'DISP' in self.deconv:
						trace.data = np.cumsum(trace.data)
						trace.taper(max_percentage=0.1, side='left', max_length=1)
						trace.detrend(type='demean')
				elif ('NZ' in trace.stats.channel) or ('NE' in trace.stats.channel) or ('NN' in trace.stats.channel):
					trace.remove_response(inventory=RS.inv, pre_filt=[0.05, 5, 0.95*self.sps, self.sps],
											output=self.deconv, water_level=4.5, taper=False)
					if 'VEL' in self.deconv:
						trace.data = np.cumsum(trace.data)
						trace.detrend(type='demean')
					elif 'DISP' in self.deconv:
						trace.data = np.cumsum(np.cumsum(trace.data))
						trace.detrend(type='linear')
					if 'ACC' not in self.deconv:
						trace.taper(max_percentage=0.1, side='left', max_length=1)

				else:
					pass	# if this is HDF


	def getq(self):
		d = self.queue.get()
		self.queue.task_done()
		if 'TERM' in str(d):
			plt.close()
			del self.queue
			if 'SELF' in str(d):
				print()
				printM('Plot has been closed, plot thread exiting.', self.sender)
			self.alive = False
			sys.exit()
		elif 'ALARM' in str(d):
			self.events += 1
			if (self.save) and (self.screencap):
				printM('Screenshot from a recent alarm has not yet been saved; saving now and resetting save timer.',
						sender=self.sender)
				self._figsave()
			self.fig.suptitle('%s.%s live output - detected events: %s' # title
							  % (self.net, self.stn, self.events),
							  fontsize=14, color=self.fgcolor, x=0.52)
			self.save = True
			self.save_timer = 0
			self.last_event = RS.UTCDateTime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
		if RS.getCHN(d) in self.chans:
			self.raw = RS.update_stream(
				stream=self.raw, d=d, fill_value='latest')
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

	def handle_close(self, evt):
		print()
		self.queue.put('TERMSELF')

	def handle_resize(self, evt=False):
		if evt:
			h = evt.height
		else:
			h = self.fig.get_size_inches()[1]*self.fig.dpi
		plt.tight_layout(pad=0, h_pad=0.1, w_pad=0,
					rect=[0.02, 0.01, 0.99, 0.91 + 0.045*(h/1080)])	# [left, bottom, right, top]

	def _figsave(self):
		self.fig.suptitle('%s.%s detected event - %s' # title
						  % (self.net, self.stn, self.last_event),
						  fontsize=14, color=self.fgcolor, x=0.52)
		self.savefig()

	def savefig(self):
		figname = os.path.join(rsudp.scap_dir, '%s.png' % datetime.utcnow().strftime('%Y-%m-%d-%H%M%S'))
		elapsed = self.save_timer / (RS.tr * RS.numchns)
		print()	# distancing from \r line
		printM('Saving plot %i seconds after last alarm' % (elapsed), sender=self.sender)
		plt.savefig(figname, facecolor=self.fig.get_facecolor(), edgecolor='none')
		print()	# distancing from \r line
		printM('Saved %s' % (figname), sender=self.sender)

	def setup_plot(self):
		"""
		Matplotlib backends are not threadsafe, so things are a little weird here.
		"""
		# instantiate a figure and set basic params
		self.fig = plt.figure(figsize=(8,3*self.num_chans))
		self.fig.canvas.mpl_connect('close_event', self.handle_close)
		self.fig.canvas.mpl_connect('resize_event', self.handle_resize)

		self.fig.canvas.set_window_title('Raspberry Shake Monitor') 
		self.fig.patch.set_facecolor(self.bgcolor)	# background color
		self.fig.suptitle('%s.%s live output%s' # title
						  % (self.net, self.stn, self.event_text),
						  fontsize=14, color=self.fgcolor,x=0.52)
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
				self.ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
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
				self.ax[s].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
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

		# rs logos
		mgr = plt.get_current_fig_manager()
		ico = pr.resource_filename('rsudp', os.path.join('img', icon))
		if qt:
			mgr.window.setWindowIcon(QtGui.QIcon(ico))
		else:
			try:
				ico = PhotoImage(file=ico)
				mgr.window.tk.call('wm', 'iconphoto', mgr.window._w, ico)
			except:
				printM('WARNING: Failed to set PNG icon image, trying .ico instead', sender=self.sender)
				try:
					ico = pr.resource_filename('rsudp', os.path.join('img', icon2))
					ico = PhotoImage(file=ico)
					mgr.window.tk.call('wm', 'iconphoto', mgr.window._w, ico)
				except:
					printM('WARNING: Failed to set icon.')

		im = mpimg.imread(pr.resource_filename('rsudp', os.path.join('img', 'version1-01-small.png')))
		#imratio = im.size[0] / im.size[1]
		scale = 0.1
		self.imax = self.fig.add_axes([0, 0.945, 0.2, 0.055], anchor='NW') # [left, bottom, right, top]
		self.imax.imshow(im, aspect='equal', interpolation='sinc')
		self.imax.axis('off')
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
			self.ax[i*self.mult].set_ylabel(self.stream[i].stats.units, color=self.fgcolor)
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

		self.handle_resize()
		# update canvas and draw
		if self.fullscreen: # set up fullscreen
			figManager = plt.get_current_fig_manager()
			if self.qt:	# maximizing in Qt
				figManager.window.showMaximized()
			else:	# maximizing in Tk
				figManager.resize(*figManager.window.maxsize())

		plt.draw()									# draw the canvas
		self.fig.canvas.start_event_loop(0.005)		# wait for canvas to update
		self.handle_resize()


	def update_plot(self):
		obstart = self.stream[0].stats.endtime - timedelta(seconds=self.seconds)	# obspy time
		start = np.datetime64(self.stream[0].stats.endtime
							  )-np.timedelta64(self.seconds, 's')	# numpy time
		end = np.datetime64(self.stream[0].stats.endtime)	# numpy time
		self.raw = self.raw.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)
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
		Any plots containing a spectrogram and more than 1 channel are drawn at most every second (1000 ms).
		All other plots are drawn at most every quarter second (250 ms).
		"""
		self.getq() # block until data is flowing from the consumer
		for i in range((self.totchns)*2): # fill up a stream object
			self.getq()
		self.set_sps()
		self.deconvolve()
		self.setup_plot()

		pkts_in_period = RS.tr * RS.numchns * self.seconds	# theoretical number of packets received in self.seconds

		n = 0	# number of iterations without plotting
		i = 0	# number of plot events without clearing the linecache
		u = -1	# number of blocked queue calls (must be -1 at startup)
		while True: # main loop
			while True:
				n += 1
				self.save_timer += 1
				if self.queue.qsize() > 0:
					self.getq()
					time.sleep(0.009)		# wait a ms to see if another packet will arrive
				else:
					u += 1 if self.getq() else 0
					if n > (self.delay * RS.numchns):
						n = 0
						break

			if i > 10:
				linecache.clearcache()
				i = 0
			else:
				i += 1
			self.stream = RS.copy(self.stream)
			self.raw = RS.copy(self.raw)
			self.deconvolve()
			self.update_plot()
			if u >= 0:				# avoiding a matplotlib broadcast error
				self.loop()

			if (self.save) and (self.save_timer > 0.6 * (pkts_in_period)):
				self.save = False
				self._figsave()
			u = 0
			time.sleep(0.005)		# wait a ms to see if another packet will arrive
			sys.stdout.flush()