import sys, os, time
import socket as s
from datetime import timedelta
import statistics
from rsudp import printM, printW, printE
from rsudp import helpers
import rsudp.raspberryshake as rs
from rsudp import COLOR
from rsudp.test import TEST

# set the terminal text color to green
COLOR['current'] = COLOR['green']

class RSAM(rs.ConsumerThread):
	"""
	.. versionadded:: 1.0.1

	A consumer class that runs an Real-time Seismic Amplitude Measurement (RSAM).
	If debugging is enabled and ``"quiet"`` is set to ``true``,
	RSAM is printed to the console every ``"interval"`` seconds,
	and optionally forwarded to an IP address and port specified by ``"fwaddr"`` and
	``"fwport"`` with packets formatted as either JSON, "lite", or CSV.

	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`.
	:param bool quiet: ``True`` to suppress printing of RSAM analysis live to the console, ``False`` otherwise.
	:param float interval: window of time in seconds to apply RSAM analysis.
	:param str cha: listening channel (defaults to [S,E]HZ)
	:param str deconv: ``'VEL'``, ``'ACC'``, ``'GRAV'``, ``'DISP'``, or ``'CHAN'``
	:param str fwaddr: Specify a forwarding address to send RSAM in a UDP packet
	:param str fwport: Specify a forwarding port to send RSAM in a UDP packet
	:param str fwformat: Specify a format for the forwarded packet: ``'LITE'``, ``'JSON'``, or ``'CSV'``
	"""

	def __init__(self, q=False, interval=5, cha='HZ', deconv=False,
				 fwaddr=False, fwport=False, fwformat='LITE', quiet=False,
				 testing=False,
				 *args, **kwargs):
		"""
		Initializes the RSAM analysis thread.
		"""
		super().__init__()
		self.sender = 'RSAM'
		self.alive = True
		self.testing = testing
		self.quiet = quiet	# suppresses printing of transmission stats
		self.stn = rs.stn
		self.fwaddr = fwaddr
		self.fwport = fwport
		self.fwformat = fwformat.upper()
		self.sock = False
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
		meanv = statistics.mean(arr)
		medianv = statistics.median(arr)
		minv = min(arr)
		maxv = max(arr)
		self.rsam = [meanv, medianv, minv, maxv]


	def _print_rsam(self):
		"""
		Print the current RSAM analysis
		"""
		if not self.quiet:
			msg = '%s Current RSAM: mean %s median %s min %s max %s' % (
				(self.stream[0].stats.starttime + timedelta(seconds=
															len(self.stream[0].data) * self.stream[0].stats.delta)).strftime('%Y-%m-%d %H:%M:%S'),
				self.rsam[0],
				self.rsam[1],
				self.rsam[2],
				self.rsam[3]
			)
			printM(msg, self.sender)

	def _forward_rsam(self):
		"""
		Send the RSAM analysis via UDP to another destination in a lightweight format
		"""
		if self.sock:
			msg = 'stn:%s|ch:%s|mean:%s|med:%s|min:%s|max:%s' % (self.stn, self.cha, self.rsam[0], self.rsam[1], self.rsam[2], self.rsam[3])
			if self.fwformat is 'JSON':
				msg = '{"station":"%s","channel":"%s","mean":%s,"median":%s,"min":%s,"max":%s}' \
					  % (self.stn, self.cha, self.rsam[0], self.rsam[1], self.rsam[2], self.rsam[3])
			elif self.fwformat is 'CSV':
				msg = '%s,%s,%s,%s,%s,%s' \
					  % (self.stn, self.cha, self.rsam[0], self.rsam[1], self.rsam[2], self.rsam[3])
			packet = bytes(msg, 'utf-8')
			self.sock.sendto(packet, (self.fwaddr, self.fwport))


	def run(self):
		"""
		Reads data from the queue and executes self.codefile if it sees an ``ALARM`` message.
		Quits if it sees a ``TERM`` message.
		"""
		if self.fwaddr and self.fwport:
			printM('Opening socket...', sender=self.sender)
			socket_type = s.SOCK_DGRAM if os.name in 'nt' else s.SOCK_DGRAM | s.SO_REUSEADDR
			self.sock = s.socket(s.AF_INET, socket_type)

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
					self._forward_rsam()
					self._print_rsam()
					next_int = time.time() + self.interval

			elif n == 0:
				printM('Starting RSAM analysis with interval=%s on station=%s channel=%s forward=%s' %
					   (self.interval, self.stn, self.cha, self.fwaddr),
					   self.sender)
			elif n == wait_pkts:
				printM('RSAM analysis up and running normally.', self.sender)
				if self.testing:
					TEST['c_rsam'][1] = True
			else:
				pass

			n += 1
			sys.stdout.flush()
