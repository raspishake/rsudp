import sys, os
from datetime import datetime, timedelta
import rsudp.raspberryshake as rs
from obspy.signal.trigger import recursive_sta_lta, trigger_onset
from rsudp import printM, printW, printE
COLOR = {}
from rsudp import COLOR
import numpy as np

# set the terminal text color to green
COLOR['current'] = COLOR['green']


class Alert(rs.ConsumerThread):
	"""
	A data consumer class that listens to a specific incoming data channel
	and calculates a recursive STA/LTA (short term average over long term 
	average). If a threshold of STA/LTA ratio is exceeded, the class
	sets the :py:data:`alarm` flag to the alarm time as a
	:py:class:`obspy.core.utcdatetime.UTCDateTime` object.
	The :py:class:`rsudp.p_producer.Producer` will see this flag
	and send an :code:`ALARM` message to the queues with the time set here.
	Likewise, when the :py:data:`alarm_reset` flag is set with a
	:py:class:`obspy.core.utcdatetime.UTCDateTime`,
	the Producer will send a :code:`RESET` message to the queues.

	:param float sta: short term average (STA) duration in seconds.
	:param float lta: long term average (LTA) duration in seconds.
	:param float thresh: threshold for STA/LTA trigger.
	:type bp: :py:class:`bool` or :py:class:`list`
	:param bp: bandpass filter parameters.
	:param bool debug: whether or not to display max STA/LTA calculation live to the console.
	:param str cha: listening channel (defaults to [S,E]HZ)
	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`

	"""
	def __init__(self, sta=5, lta=30, thresh=1.6, reset=1.55, bp=False,
				 debug=True, cha='HZ', q=False, sound=False, deconv=False,
				 *args, **kwargs):
		
		"""
		Initializing the alert thread with parameters to set up the recursive
		STA-LTA trigger, filtering, and the channel used for listening.

		"""
		super().__init__()
		self.sender = 'Alert'
		self.alive = True

		if q:
			self.queue = q
		else:
			printE('no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			sys.exit()

		self.default_ch = 'HZ'
		self.sta = sta
		self.lta = lta
		self.thresh = thresh
		self.reset = reset
		self.debug = debug
		self.args = args
		self.kwargs = kwargs
		self.raw = rs.Stream()
		self.stream = rs.Stream()
		cha = self.default_ch if (cha == 'all') else cha
		self.cha = cha if isinstance(cha, str) else cha[0]
		self.sps = rs.sps
		self.inv = rs.inv
		self.stalta = np.ndarray(1)
		self.maxstalta = 0
		self.units = 'counts'
		
		deconv = deconv.upper() if deconv else False
		self.deconv = self.deconv if (deconv in rs.UNITS) else False
		if self.deconv and rs.inv:
			self.units = '%s (%s)' % (rs.UNITS[0], rs.UNITS[1]) if (self.deconv in rs.UNITS) else self.units
			printM('Signal deconvolution set to %s' % (self.deconv), self.sender)
		else:
			self.units = rs.UNITS['CHAN'][1]
			self.deconv = False
		printM('Alert stream units are %s' % (self.units.strip(' ').lower()), self.sender)

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

		if self.cha not in str(rs.chns):
			printE('Could not find channel %s in list of channels! Please correct and restart.' % self.cha, self.sender)
			sys.exit(2)

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
		'''
		Reads data from the queue and updates the stream.

		:rtype: bool
		:return: Returns ``True`` if stream is updated, otherwise ``False``.
		'''
		d = self.queue.get(True, timeout=None)
		self.queue.task_done()
		if self.cha in str(d):
			self.raw = rs.update_stream(stream=self.raw, d=d, fill_value='latest')
			return True
		elif 'TERM' in str(d):
			self.alive = False
			printM('Exiting.', self.sender)
			sys.exit()
		else:
			return False

	def _deconvolve(self):
		'''
		Deconvolves the stream associated with this class.
		'''
		rs.deconvolve(self)

	def run(self):
		"""
		Reads data from the queue into a :class:`obspy.core.stream.Stream` object,
		then runs a :func:`obspy.signal.trigger.recursive_sta_lta` function to
		determine whether to raise an alert flag (:py:data:`rsudp.c_alert.Alert.alarm`).
		The producer reads this flag and uses it to notify other consumers.
		"""
		n = 0

		wait_pkts = (self.lta) / (rs.tf / 1000)

		while n > 3:
			self.getq()
			n += 1

		n = 0
		while True:
			while True:
				if self.queue.qsize() > 0:
					self._getq()			# get recent packets
				else:
					if self._getq():		# is this the specified channel? if so break
						break

			self.raw = rs.copy(self.raw)	# necessary to avoid memory leak
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
						# raise a flag that the Producer can read and modify 
						self.alarm = rs.fsec(self.stream[0].stats.starttime + timedelta(seconds=
									 		 trigger_onset(self.stalta, self.thresh,
											 self.reset)[-1][0] * self.stream[0].stats.delta))
						self.exceed = True	# the state machine; this one should not be touched from the outside, otherwise bad things will happen
						print()
						printM('Trigger threshold of %s exceeded at %s'
							   % (self.thresh, self.alarm.strftime('%Y-%m-%d %H:%M:%S.%f')[:22]), self.sender)
						printM('Trigger will reset when STA/LTA goes below %s...' % self.reset, sender=self.sender)
						COLOR['current'] = COLOR['purple']
					else:
						pass

					if self.stalta.max() > self.maxstalta:
						self.maxstalta = self.stalta.max()

				else:
					if self.exceed:
						if self.stalta[-1] < self.reset:
							self.alarm_reset = rs.fsec(self.stream[0].stats.endtime)	# lazy; effective
							self.exceed = False
							print()
							printM('Max STA/LTA ratio reached in alarm state: %s' % (round(self.maxstalta, 3)),
									self.sender)
							printM('Earthquake trigger reset and active again at %s' % (
								   self.alarm_reset.strftime('%Y-%m-%d %H:%M:%S.%f')[:22]),
								   self.sender)
							self.maxstalta = 0
							COLOR['current'] = COLOR['green']
					else:
						pass
				self.stream = rs.copy(self.stream)
				if self.debug:
					msg = '\r%s [%s] Threshold: %s; Current max STA/LTA: %.4f' % (
							(self.stream[0].stats.starttime + timedelta(seconds=
							len(self.stream[0].data) * self.stream[0].stats.delta)).strftime('%Y-%m-%d %H:%M:%S'),
							self.sender,
							self.thresh,
							round(np.max(self.stalta[-50:]), 4)
							)
					print(COLOR['current'] + COLOR['bold'] + msg + COLOR['white'], end='', flush=True)
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
