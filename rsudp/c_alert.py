import sys, os
from threading import Thread
from datetime import datetime, timedelta
import rsudp.raspberryshake as RS
from obspy.signal.trigger import recursive_sta_lta
from rsudp import printM
import numpy as np


class Alert(Thread):
	"""
	A data consumer class that listens to a specific incoming data channel
	and calculates a recursive STA/LTA (short term average over long term 
	average). If a threshold of STA/LTA ratio is exceeded, the class
	activates a function of the user's choosing. By default, the function
	simply prints a message to the terminal window, but the user can
	choose to run a function of their own as well.
	"""
	def __init__(self, sta=5, lta=30, thresh=1.6, reset=1.55, bp=False,
				 debug=True, cha='HZ', win_ovr=False, q=False, func=None,
				 sound=False, deconv=False,
				 *args, **kwargs):
		
		"""
		Initialize the alert thread with parameters to set up the recursive
		STA-LTA trigger, filtering, the function that is executed upon
		trigger activation, and the channel used for listening.

		:param float sta: short term average (STA) duration in seconds
		:param float lta: long term average (LTA) duration in seconds
		:param float thresh: threshold for STA/LTA trigger
		:type bp: :py:class:`bool` or :py:class:`list`
		:param bp: bandpass filter parameters
		:param func func: threshold for STA/LTA trigger
		:param bool debug: threshold for STA/LTA trigger
		:param str cha: listening channel (defaults to [S,E]HZ)
		"""
		super().__init__()
		self.sender = 'Alert'
		self.alive = True

		if q:
			self.queue = q
		else:
			printM('ERROR: no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			sys.exit()

		self.default_ch = 'HZ'
		self.sta = sta
		self.lta = lta
		self.thresh = thresh
		self.reset = reset
		self.func = func
		self.win_ovr = win_ovr
		self.debug = debug
		self.args = args
		self.kwargs = kwargs
		self.raw = RS.Stream()
		self.stream = RS.Stream()
		cha = self.default_ch if (cha == 'all') else cha
		self.cha = cha if isinstance(cha, str) else cha[0]
		self.sps = RS.sps
		self.inv = RS.inv
		self.stalta = np.ndarray(1)
		self.maxstalta = 0

		self.deconv = deconv if (deconv == 'ACC') or (deconv == 'VEL') or (deconv == 'DISP') else False
		if self.deconv and RS.inv:
			deconv = deconv.upper()
			self.units = 'Acceleration (m/s$^2$)' if (self.deconv == 'ACC') else False
			self.units = 'Velocity (m/s)' if (self.deconv == 'VEL') else self.units
			self.units = 'Displacement (m)' if (self.deconv == 'DISP') else self.units
			printM('Signal deconvolution set to %s' % (self.deconv), self.sender)
		else:
			self.units = 'Voltage counts'
			self.deconv = False
		printM('Alert stream units are %s' % (self.units), self.sender)

		self.alarm = False
		self.exceed = False
		self.sound = sound
		if bp:
			self.freqmin = bp[0]
			self.freqmax = bp[1]
			self.freq = 0
			if (bp[0] <= 0) and (bp[1] >= (self.sps/2)):
				self.filt = False
			elif (bp[0] > 0) and (bp[1] >= (self.sps/2)):
				self.filt = 'highpass'
				self.freq = bp[0]
				desc = 'low corner %s' % (bp[0])
			elif (bp[0] <= 0) and (bp[1] <= (self.sps/2)):
				self.filt = 'lowpass'
				self.freq = bp[1]
			else:
				self.filt = 'bandpass'
		else:
			self.filt = False

		if self.cha not in str(RS.chns):
			printM('ERROR: Could not find channel %s in list of channels! Please correct and restart.' % self.cha, self.sender)
			sys.exit(2)

		if (os.name in 'nt') and (not callable(self.func)) and (not self.win_ovr):
			printM('ERROR: Using Windows with custom alert code! Your code MUST have UNIX/Mac newline characters!')
			printM('       Please use a conversion tool like dos2unix to convert line endings')
			printM('       (https://en.wikipedia.org/wiki/Unix2dos) to make your code file')
			printM('       readable to the Python interpreter.')
			printM('       Once you have done that, please set "win_override" to true')
			printM('       in the settings file.')
			printM('       (see also footnote [1] on this page: https://docs.python.org/3/library/functions.html#id2)')
			printM('THREAD EXITING, please correct and restart!', self.sender)
			sys.exit(2)
		else:
			pass

		listen_ch = '?%s' % self.cha
		printM('Starting Alert trigger with sta=%ss, lta=%ss, and threshold=%s on channel=%s'
				% (self.sta, self.lta, self.thresh, listen_ch), self.sender)
		if self.filt == 'bandpass':
			printM('Alert stream will be %s filtered from %s to %s Hz'
					% (self.filt, self.freqmin, self.freqmax), self.sender)
		elif self.filt in ('lowpass', 'highpass'):
			modifier = 'below' if self.filt in 'lowpass' else 'above'
			printM('Alert stream will be %s filtered %s %s Hz'
					% (self.filt, modifier, self.freq), self.sender)

	def _getq(self):
		d = self.queue.get(True, timeout=None)
		self.queue.task_done()
		if self.cha in str(d):
			self.raw = RS.update_stream(stream=self.raw, d=d, fill_value='latest')
			return True
		elif 'TERM' in str(d):
			self.alive = False
			printM('Exiting.', self.sender)
			sys.exit()
		else:
			return False

	def _deconvolve(self):
		RS.deconvolve(self)

	def run(self):
		"""

		"""
		n = 0

		wait_pkts = (self.lta) / (RS.tf / 1000)

		while n > 3:
			self.getq()
			n += 1

		n = 0
		while True:
			while True:
				if self.queue.qsize() > 0:
					self._getq()		# get recent packets
				else:
					if self._getq():	# is this the specified channel? if so break
						break

			self.raw = RS.copy(self.raw)
			self.stream = self.raw.copy()
			if self.deconv:
				self._deconvolve()

			if n > wait_pkts:
				obstart = self.stream[0].stats.endtime - timedelta(seconds=self.lta)	# obspy time
				self.raw = self.raw.slice(starttime=obstart)		# slice the stream to the specified length (seconds variable)
				self.stream = self.stream.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)

				if self.filt:
					if self.filt in 'bandpass':
						self.stalta = recursive_sta_lta(
									self.stream[0].copy().filter(type=self.filt,
									freqmin=self.freqmin, freqmax=self.freqmax),
									int(self.sta * self.sps), int(self.lta * self.sps))
					else:
						self.stalta = recursive_sta_lta(
									self.stream[0].copy().filter(type=self.filt,
									freq=self.freq),
									int(self.sta * self.sps), int(self.lta * self.sps))

				else:
					self.stalta = recursive_sta_lta(self.stream[0],
							int(self.sta * self.sps), int(self.lta * self.sps))
				if self.stalta.max() > self.thresh:
					if not self.exceed:
						print(); print()
						self.alarm = True	# raise a flag that the Producer can read and modify 
						self.exceed = True	# the state machine; this one should not be touched from the outside, otherwise bad things will happen
						printM('Trigger threshold of %s exceeded: %s'
								% (self.thresh, round(self.stalta.max(), 3)), self.sender)
						if callable(self.func):
							self.func(sound=self.sound, *self.args, **self.kwargs)
						else:
							printM('Attempting execution of custom script. If something goes wrong, you may need to kill this process manually...')
							try:
								exec(self.func)
							except Exception as e:
								printM('Execution failed, error: %s' % e)
						printM('Trigger will reset when STA/LTA goes below %s...' % self.reset, sender=self.sender)
					else:
						pass

					if self.stalta.max() > self.maxstalta:
						self.maxstalta = self.stalta.max()

				else:
					if self.exceed:
						if self.stalta[-1] < self.reset:
							self.exceed = False
							print()
							printM('Max STA/LTA ratio reached in alarm state: %s' % (round(self.maxstalta, 3)),
									self.sender)
							printM('Earthquake trigger reset and active again.',
									self.sender)
							self.maxstalta = 0
					else:
						pass
				self.stream = RS.copy(self.stream)
				print('\r%s [%s] Threshold: %s; Current max STA/LTA: %.4f'
					  % (datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), self.sender,
					  self.thresh, round(np.max(self.stalta[-50:]), 4)), end='', flush=True)
			elif n == 0:
				printM('Listening to channel %s'
						% (self.stream[0].stats.channel), self.sender)
				printM('Earthquake trigger warmup time of %s seconds...'
						% (self.lta), self.sender)
			elif n == wait_pkts:
				printM('Earthquake trigger up and running normally.',
						self.sender)
			else:
				pass

			n += 1
			sys.stdout.flush()
