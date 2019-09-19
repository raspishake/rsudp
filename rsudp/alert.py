import sys
from threading import Thread
from queue import Queue
from datetime import datetime, timedelta
import rsudp.raspberryshake as RS
from rsudp.raspberryshake import qsize
from rsudp.consumer import destinations
from obspy.signal.trigger import recursive_sta_lta
from rsudp import printM
import numpy as np


class Alert(Thread):
	def __init__(self, sta=5, lta=30, thresh=1.6, bp=False, func='print',
				 debug=True, cha='HZ', *args, **kwargs):
		
		"""
		A recursive STA-LTA 
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
			if (bp[0] <= 0) and (bp[1] >= (sps/2)):
				self.filt = False
			elif (bp[0] > 0) and (bp[1] >= (sps/2)):
				self.filt = 'highpass'
				self.freq = bp[0]
			elif (bp[0] <= 0) and (bp[1] <= (sps/2)):
				self.filt = 'lowpass'
				self.freq = bp[1]
			else:
				self.filt = 'bandpass'
		else:
			self.filt = False

		alrtq = Queue(qsize)
		destinations.append(alrtq)
		self.qno = len(destinations) - 1

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
					cft = recursive_sta_lta(self.stream[0].filter(
								type=self.filt, freq=self.freq,
								freqmin=self.freqmin, freqmax=self.freqmax),
								int(self.sta * self.sps), int(self.lta * self.sps))
				else:
					cft = recursive_sta_lta(self.stream[0],
							int(self.sta * self.sps), int(self.lta * self.sps))
				if cft.max() > self.thresh:
					if self.func == 'print':
						print()
						printM('Event detected! Trigger threshold: %s, CFT: %s '
								% (self.thresh, cft.max()), self.sender)
						printM('Waiting %s sec for clear trigger'
								% (self.lta), self.sender)
					else:
						print()
						printM('Trigger threshold of %s exceeded: %s'
								% (self.thresh, cft.max()), self.sender)
						self.func(*self.args, **self.kwargs)
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
					printM('Max CFT reached in alarm state: %s' % (maxcft),
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
