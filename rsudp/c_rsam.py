import sys, time
from datetime import datetime, timedelta
import statistics
from rsudp import printM, printW, printE
from rsudp import helpers
import rsudp.raspberryshake as rs
COLOR = {}
from rsudp import COLOR

# set the terminal text color to green
COLOR['current'] = COLOR['green']

class RSAM(rs.ConsumerThread):
	"""
	.. versionadded:: 1.0.0

	A consumer class that runs an Real-time Seismic Analysis Measurement (RSAM).

	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`.
	:param bool debug: whether or not to display RSAM analysis live to the console.
	:param float interval: window of time in seconds to apply RSAM analysis.
	:param str cha: listening channel (defaults to [S,E]HZ)
	:param str deconv: ``'VEL'``, ``'ACC'``, ``'GRAV'``, ``'DISP'``, or ``'CHAN'``
	"""

	def __init__(self, q=False, debug=False, interval=5, cha='HZ', deconv=False, *args, **kwargs):
		"""
		Initializes the RSAM analysis thread.
		"""
		super().__init__()
		self.sender = 'RSAM'
		self.alive = True
		self.debug = debug
		self.interval = interval
		self.default_ch = 'HZ'
		self.args = args
		self.kwargs = kwargs
		self.raw = rs.Stream()
		self.stream = rs.Stream()
		self.units = 'counts'

		self._set_deconv(deconv)

		self._set_channel(cha)

		self.rsam = [1, 1, 1]

		if q:
			self.queue = q
		else:
			printE('no queue passed to the consumer thread! We will exit now!',
				   self.sender)
			sys.stdout.flush()
			self.alive = False
			sys.exit()

		printM('Starting.', self.sender)


	def _set_deconv(self, deconv):
		"""
		This function sets the deconvolution units. Allowed values are as follows:

		.. |ms2| replace:: m/s\ :sup:`2`\

		- ``'VEL'`` - velocity (m/s)
		- ``'ACC'`` - acceleration (|ms2|)
		- ``'GRAV'`` - fraction of acceleration due to gravity (g, or 9.81 |ms2|)
		- ``'DISP'`` - displacement (m)
		- ``'CHAN'`` - channel-specific unit calculation, i.e. ``'VEL'`` for geophone channels and ``'ACC'`` for accelerometer channels

		:param str deconv: ``'VEL'``, ``'ACC'``, ``'GRAV'``, ``'DISP'``, or ``'CHAN'``
		"""
		deconv = deconv.upper() if deconv else False
		self.deconv = deconv if (deconv in rs.UNITS) else False
		if self.deconv and rs.inv:
			self.units = '%s (%s)' % (rs.UNITS[self.deconv][0], rs.UNITS[self.deconv][1]) if (self.deconv in rs.UNITS) else self.units
			printM('Signal deconvolution set to %s' % (self.deconv), self.sender)
		else:
			self.units = rs.UNITS['CHAN'][1]
			self.deconv = False
		printM('RSAM stream units are %s' % (self.units.strip(' ').lower()), self.sender)


	def _find_chn(self):
		"""
		Finds channel match in list of channels.
		"""
		for chn in rs.chns:
			if self.cha in chn:
				self.cha = chn


	def _set_channel(self, cha):
		"""
		This function sets the channel to listen to. Allowed values are as follows:

		- "SHZ"``, ``"EHZ"``, ``"EHN"`` or ``"EHE"`` - velocity channels
		- ``"ENZ"``, ``"ENN"``, ``"ENE"`` - acceleration channels
		- ``"HDF"`` - pressure transducer channel
		- ``"all"`` - resolves to either ``"EHZ"`` or ``"SHZ"`` if available

		:param cha: the channel to listen to
		:type cha: str
		"""
		cha = self.default_ch if (cha == 'all') else cha
		self.cha = cha if isinstance(cha, str) else cha[0]

		if self.cha in str(rs.chns):
			self._find_chn()
		else:
			printE('Could not find channel %s in list of channels! Please correct and restart.' % self.cha, self.sender)
			sys.exit(2)


	def _getq(self):
		"""
		Reads data from the queue and updates the stream.

		:rtype: bool
		:return: Returns ``True`` if stream is updated, otherwise ``False``.
		"""
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
		"""
		Deconvolves the stream associated with this class.
		"""
		if self.deconv:
			helpers.deconvolve(self)


	def _subloop(self):
		"""
		Gets the queue and figures out whether or not the specified channel is in the packet.
		"""
		while True:
			if self.queue.qsize() > 0:
				self._getq()			# get recent packets
			else:
				if self._getq():		# is this the specified channel? if so break
					break


	def _rsam(self):
		"""
		Run the RSAM analysis
		"""
		arr = [abs(el) for el in self.stream[0].data]
		minv = min(arr)
		maxv = max(arr)
		meanv = statistics.mean(arr)
		self.rsam = [minv, maxv, meanv]


	def _print_rsam(self):
		"""
		Print the current RSAM analysis
		"""
		if self.debug:
			msg = '%s [%s] Current RSAM: min %s max %s mean %s' % (
				(self.stream[0].stats.starttime + timedelta(seconds=
															len(self.stream[0].data) * self.stream[0].stats.delta)).strftime('%Y-%m-%d %H:%M:%S'),
				self.sender,
				self.rsam[0],
				self.rsam[1],
				self.rsam[2],
			)
			printM(msg, self.sender)


	def run(self):
		"""
		Reads data from the queue and executes self.codefile if it sees an ``ALARM`` message.
		Quits if it sees a ``TERM`` message.
		"""
		n = 0
		next_int = time.time() + self.interval

		wait_pkts = self.interval / (rs.tf / 1000)

		while n > 3:
			self.getq()
			n += 1

		n = 0
		while True:
			self._subloop()

			self.raw = rs.copy(self.raw)	# necessary to avoid memory leak
			self.stream = self.raw.copy()
			self._deconvolve()

			if n > wait_pkts:
				# if the trigger is activated
				obstart = self.stream[0].stats.endtime - timedelta(seconds=self.interval)	# obspy time
				self.raw = self.raw.slice(starttime=obstart)		# slice the stream to the specified length (seconds variable)
				self.stream = self.stream.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)

				# run rsam analysis
				if time.time() > next_int:
					self._rsam()
					self.stream = rs.copy(self.stream)  # prevent mem leak
					self._print_rsam()
					next_int = time.time() + self.interval

			elif n == 0:
				printM('Starting RSAM analysis with interval=%s on channel=%s' % (self.interval, self.cha), self.sender)
			elif n == wait_pkts:
				printM('RSAM analysis up and running normally.', self.sender)
			else:
				pass

			n += 1
			sys.stdout.flush()
