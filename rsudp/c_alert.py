import sys, os
from threading import Thread
from queue import Queue
from datetime import datetime, timedelta
import rsudp.raspberryshake as RS
from rsudp.raspberryshake import qsize
from rsudp.c_consumer import destinations
from obspy.signal.trigger import recursive_sta_lta
from rsudp import printM
import numpy as np


class Alert(Thread):
	"""
	An consumer class that listens to a specific incoming data channel
	and calculates a recursive STA/LTA (short term average over long term 
	average). If a threshold of STA/LTA ratio is exceeded, the class
	activates a function of the user's choosing. By default, the function
	simply prints a message to the terminal window, but the user can
	choose to run a function of their own as well.
	"""
	def __init__(self, sta=5, lta=30, thresh=1.6, bp=False, func=None,
				 debug=True, cha='HZ', win_ovr=False, *args, **kwargs):
		
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
		global destinations
		self.default_ch = 'HZ'
		self.sta = sta
		self.lta = lta
		self.thresh = thresh
		self.func = func
		self.win_ovr = win_ovr
		self.debug = debug
		self.args = args
		self.kwargs = kwargs
		self.stream = RS.Stream()
		cha = self.default_ch if (cha == 'all') else cha
		self.cha = cha if isinstance(cha, str) else cha[0]
		self.sps = RS.sps
		self.inv = RS.inv
		self.sender = 'Alert'
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

		alrtq = Queue(qsize)
		destinations.append(alrtq)
		self.qno = len(destinations) - 1

		if (os.name in 'nt') and (not callable(self.func)) and (not self.win_ovr):
			printM('ERROR: Using Windows with custom alert code! Your code MUST have UNIX/Mac newline characters!')
			print('                                   Please use a conversion tool like dos2unix to convert line endings')
			print('                                   (https://en.wikipedia.org/wiki/Unix2dos) to make your code file')
			print('                                   readable to the Python interpreter.')
			print('                                   Once you have done that, please set "win_override" to true')
			print('                                   in the settings file.')
			print('            (see also footnote [1] on this page: https://docs.python.org/3/library/functions.html#id2)')
			printM('THREAD EXITING, please correct and restart!', self.sender)
			sys.exit(2)
		else:
			pass

		listen_ch = '?%s' % self.default_ch if self.cha == self.default_ch else self.cha
		printM('Starting Alert trigger with sta=%ss, lta=%ss, and threshold=%s on channel=%s'
				% (self.sta, self.lta, self.thresh, listen_ch), self.sender)
		if self.filt == 'bandpass':
			printM('Alert stream will be %s filtered from %s to %s Hz'
					% (self.filt, self.freqmin, self.freqmax), self.sender)
		elif self.filt in ('lowpass', 'highpass'):
			modifier = 'below' if self.filt in 'lowpass' else 'above'
			printM('Alert stream will be %s filtered %s %s Hz'
					% (self.filt, modifier, self.freq), self.sender)

	def getq(self):
		d = destinations[self.qno].get(True, timeout=None)
		destinations[self.qno].task_done()
		if self.cha in str(d):
			self.stream = RS.update_stream(
				stream=self.stream, d=d, fill_value='latest')
			return True
		elif 'TERM' in str(d):
			sys.exit()
		else:
			return False
	
	def set_sps(self):
		self.sps = self.stream[0].stats.sampling_rate

	def run(self):
		"""

		"""
		cft, maxcft = np.zeros(1), 0
		n = 0

		wait_pkts = (self.lta) / (RS.tf / 1000)

		while n > 3:
			self.getq()
			n += 1

		n = 0
		while True:
			while True:
				if destinations[self.qno].qsize() > 0:
					self.getq()		# get recent packets
				else:
					if self.getq():	# is this the specified channel? if so break
						break

			if n > wait_pkts:
				obstart = self.stream[0].stats.endtime - timedelta(
							seconds=self.lta)	# obspy time
				self.stream = self.stream.slice(
							starttime=obstart)	# slice the stream to the specified length (seconds variable)

				if self.filt:
					if self.filt in 'bandpass':
						cft = recursive_sta_lta(
									self.stream[0].copy().filter(type=self.filt,
									freqmin=self.freqmin, freqmax=self.freqmax),
									int(self.sta * self.sps), int(self.lta * self.sps))
					else:
						cft = recursive_sta_lta(
									self.stream[0].copy().filter(type=self.filt,
									freq=self.freq),
									int(self.sta * self.sps), int(self.lta * self.sps))

				else:
					cft = recursive_sta_lta(self.stream[0],
							int(self.sta * self.sps), int(self.lta * self.sps))
				if cft.max() > self.thresh:
					print()
					printM('Trigger threshold of %s exceeded: %s'
							% (self.thresh, cft.max()), self.sender)
					if callable(self.func):
						self.func(*self.args, **self.kwargs)
					else:
						printM('Attempting execution of custom script...')
						try:
							exec(self.func)
						except Exception as e:
							printM('Execution failed, error: %s' % e)
					n = 1
				self.stream = RS.copy(self.stream)

			elif n == 0:
				printM('Listening to channel %s'
						% (self.stream[0].stats.channel), self.sender)
				printM('Earthquake trigger warmup time of %s seconds...'
						% (self.lta), self.sender)
				n += 1
			elif n == wait_pkts:
				if cft.max() == 0:
					printM('Earthquake trigger up and running normally.',
							self.sender)
				else:
					printM('Max STA/LTA ratio reached in alarm state: %s' % (maxcft),
							self.sender)
					printM('Earthquake trigger reset and active again.',
							self.sender)
					maxcft = 0
				n += 1
			else:
				if cft.max() > maxcft:
					maxcft = cft.max()
				n += 1
			sys.stdout.flush()
