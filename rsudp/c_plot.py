import os, sys, platform
import pkg_resources as pr
import time
import math
import numpy as np
from datetime import datetime, timedelta
import rsudp.raspberryshake as RS
from rsudp import printM
import rsudp
import linecache
sender = 'plot.py'
qt = False
try:		# test for matplotlib and exit if import fails
	from matplotlib import use
	try:	# no way to know what machines can handle what software, but Tk is more universal
		use('Qt5Agg')	# try for Qt because it's better and has less threatening errors
		from PyQt5 import QtGui
		qt = True
	except Exception as e:
		printM('WARNING: Qt import failed. Trying Tk...')
		printM('error detail: %s' % e)
		try:	# fail over to the more reliable Tk
			use('TkAgg')
			from tkinter import PhotoImage
		except Exception as e:
			printM('ERROR: Could not import either Qt or Tk, and the plot module requires at least one of them to run.', sender)
			printM('Please make sure either PyQt5 or Tkinter is installed.', sender)
			printM('error detail: %s'% e, sender)
			raise ImportError('Could not import either Qt or Tk, and the plot module requires at least one of them to run')
	import matplotlib.pyplot as plt
	import matplotlib.dates as mdates
	import matplotlib.image as mpimg
	from matplotlib import rcParams
	from matplotlib.ticker import EngFormatter
	rcParams['toolbar'] = 'None'
	plt.ion()
	mpl = True
	import warnings
	warnings.filterwarnings("ignore", module="matplotlib")
except Exception as e:
	printM('ERROR: Could not import matplotlib, plotting will not be available.', sender)
	printM('error detail: %s' % e, sender)
	mpl = False

icon = 'icon.ico'
icon2 = 'icon.png'

class Plot:
	def __init__(self, cha='all', q=False,
				 seconds=30, spectrogram=False,
				 fullscreen=False, kiosk=False,
				 qt=qt, deconv=False,
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
			printM('WARNING: Running on %s machine, using Tk instead of Qt' % (platform.machine()), self.sender)
		if q:
			self.queue = q
		else:
			printM('ERROR: no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			sys.exit()

		self.master_queue = None	# careful with this, this goes directly to the master consumer. gets set by main thread.
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
		self.pkts_in_period = RS.tr * RS.numchns * self.seconds	# theoretical number of packets received in self.seconds
		self.spectrogram = spectrogram

		self.deconv = deconv if (deconv == 'ACC') or (deconv == 'VEL') or (deconv == 'DISP') or (deconv == 'CHAN') else False
		if self.deconv and RS.inv:
			deconv = deconv.upper()
			if self.deconv in 'ACC':
				self.units = 'Acceleration'
				self.unit = 'm/s$^2$'
			if self.deconv in 'VEL':
				self.units = 'Velocity'
				self.unit = 'm/s'
			if self.deconv in 'DISP':
				self.units = 'Displacement'
				self.unit = 'm'
			if self.deconv in 'CHAN':
				self.units = 'channel-specific'
				self.unit = 'counts'
			printM('Signal deconvolution set to %s' % (self.deconv), self.sender)
		else:
			self.units = 'Voltage counts'
			self.unit = ' counts'
			self.deconv = False
		printM('Seismogram units are %s' % (self.units), self.sender)

		self.per_lap = 0.9
		self.fullscreen = fullscreen
		self.kiosk = kiosk
		self.qt = qt
		self.num_chans = len(self.chans)
		self.delay = RS.tr if (self.spectrogram) else 1
		self.delay = 0.5 if (self.chans == ['SHZ']) else self.delay

		self.screencap = screencap
		self.save_timer = 0
		self.save_pct = 0.7
		self.save = []
		self.events = 0
		self.event_text = ' - detected events: 0' if alert else ''
		self.last_event = []
		self.last_event_str = False
		# plot stuff
		self.bgcolor = '#202530' # background
		self.fgcolor = '0.8' # axis and label color
		self.linecolor = '#c28285' # seismogram color

	def deconvolve(self):
		RS.deconvolve(self)

	def getq(self):
		d = self.queue.get()
		self.queue.task_done()
		if 'TERM' in str(d):
			plt.close()
			if 'SELF' in str(d):
				print()
				printM('Plot has been closed, plot thread will exit.', self.sender)
			self.alive = False
			RS.producer = False

		elif 'ALARM' in str(d):
			self.events += 1		# add event to count
			self.save_timer -= 1	# don't push the save time forward if there are a large number of alarm events
			event = [self.save_timer + int(self.save_pct*self.pkts_in_period),
					 RS.UTCDateTime.strptime(d.decode('utf-8'), 'ALARM %Y-%m-%dT%H:%M:%S.%fZ')]	# event = [save after count, datetime]
			self.last_event_str = event[1].strftime('%Y-%m-%d %H:%M:%S UTC')
			printM('Event time: %s' % (self.last_event_str), self.sender)		# show event time in the logs
			if self.screencap:
				print()
				printM('Saving png in about %i seconds' % (self.save_pct * (self.seconds)), self.sender)
				self.save.append(event) # append 
			self.fig.suptitle('%s.%s live output - detected events: %s' # title
							% (self.net, self.stn, self.events),
							fontsize=14, color=self.fgcolor, x=0.52)
			self.fig.canvas.set_window_title('(%s) %s.%s - Raspberry Shake Monitor' % (self.events, self.net, self.stn))

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
		self.queue.put(b'TERMSELF')

	def handle_resize(self, evt=False):
		if evt:
			h = evt.height
		else:
			h = self.fig.get_size_inches()[1]*self.fig.dpi
		plt.tight_layout(pad=0, h_pad=0.1, w_pad=0,
					rect=[0.02, 0.01, 0.98, 0.90 + 0.045*(h/1080)])	# [left, bottom, right, top]

	def _eventsave(self):
		self.save.reverse()
		event = self.save.pop()
		self.save.reverse()

		event_time_str = event[1].strftime('%Y-%m-%d-%H%M%S')		# event time
		title_time_str = event[1].strftime('%Y-%m-%d %H:%M:%S')

		# change title (just for a moment)
		self.fig.suptitle('%s.%s detected event - %s UTC' # title
						  % (self.net, self.stn, title_time_str),
						  fontsize=14, color=self.fgcolor, x=0.52)

		# save figure
		self.savefig(event_time=event[1], event_time_str=event_time_str)

		# reset title
		self._set_fig_title()


	def savefig(self, event_time=RS.UTCDateTime.now(),
				event_time_str=RS.UTCDateTime.now().strftime('%Y-%m-%d-%H%M%S')):
		figname = os.path.join(rsudp.scap_dir, '%s-%s.png' % (self.stn, event_time_str))
		elapsed = RS.UTCDateTime.now() - event_time
		if int(elapsed) > 0:
			print()	# distancing from \r line
			printM('Saving png %i seconds after alarm' % (elapsed), sender=self.sender)
		plt.savefig(figname, facecolor=self.fig.get_facecolor(), edgecolor='none')
		print()	# distancing from \r line
		printM('Saved %s' % (figname), sender=self.sender)
		printM('%s thread has saved an image, sending IMGPATH message to queues' % self.sender, sender=self.sender)
		self.master_queue.put(b'IMGPATH %s %s' % (bytes(str(event_time), 'utf-8'), bytes(str(figname), 'utf-8')))

	def _set_fig_title(self):
		self.fig.suptitle('%s.%s live output - detected events: %s' # title
						  % (self.net, self.stn, self.events),
						  fontsize=14, color=self.fgcolor, x=0.52)


	def setup_plot(self):
		"""
		Matplotlib backends are not threadsafe, so things are a little weird.
		"""
		# instantiate a figure and set basic params
		self.fig = plt.figure(figsize=(10,3*self.num_chans))
		self.fig.canvas.mpl_connect('close_event', self.handle_close)
		self.fig.canvas.mpl_connect('resize_event', self.handle_resize)
		
		if qt:
			self.fig.canvas.window().statusBar().setVisible(False) # remove bottom bar
		self.fig.canvas.set_window_title('%s.%s - Raspberry Shake Monitor' % (self.net, self.stn))
		self.fig.patch.set_facecolor(self.bgcolor)	# background color
		self.fig.suptitle('%s.%s live output%s'	# title
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
				self.ax[0].yaxis.set_major_formatter(EngFormatter(unit=self.unit))
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
				self.ax[s].yaxis.set_major_formatter(EngFormatter(unit=self.unit))
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
		self.imax = self.fig.add_axes([0.015, 0.944, 0.2, 0.056], anchor='NW') # [left, bottom, right, top]
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
		figManager = plt.get_current_fig_manager()
		if self.kiosk:
			figManager.full_screen_toggle()
		else:
			if self.fullscreen:	# set fullscreen
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
			if self.deconv:
				if (self.deconv in 'CHAN'):
					ch = self.stream[i].stats.channel
					if ('HZ' in ch) or ('HN' in ch) or ('HE' in ch):
						unit = 'm/s'
					elif ('EN' in ch):
						unit = 'm/s$^2$'
					else:
						unit = ' counts'
					self.ax[i*self.mult].yaxis.set_major_formatter(EngFormatter(unit=unit))

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

		n = 0	# number of iterations without plotting
		i = 0	# number of plot events without clearing the linecache
		u = -1	# number of blocked queue calls (must be -1 at startup)
		while True: # main loop
			while True:
				if self.alive == False:	# break if the user has closed the plot
					break
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

			if self.alive == False:	# break if the user has closed the plot
				printM('Exiting.', self.sender)
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

			if self.save:
				if (self.save_timer > self.save[0][0]):
					self._eventsave()
			u = 0
			time.sleep(0.005)		# wait a ms to see if another packet will arrive
			sys.stdout.flush()
		return
