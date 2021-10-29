import sys, os
import time
from datetime import timedelta
from obspy import UTCDateTime
import rsudp.raspberryshake as rs
from rsudp import printM, printW, printE, helpers
from rsudp.test import TEST

class Write(rs.ConsumerThread):
	"""
	A simple routine to write daily miniSEED data to :code:`output_dir/data`.

	:param cha: channel(s) to forward. others will be ignored.
	:type cha: str or list
	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`
	:param bool debug: whether or not to display messages when writing data to disk.
	"""
	def __init__(self, q, data_dir, testing=False, debug=False, cha='all'):
		"""
		Initialize the process
		"""
		super().__init__()
		self.sender = 'Write'
		self.alive = True
		self.testing = testing
		self.debug = debug
		if self.testing:
			self.debug = True

		self.queue = q

		self.stream = rs.Stream()
		self.outdir = os.path.join(data_dir, 'data')
		self.outfiles = []

		self.chans = []
		helpers.set_channels(self, cha)

		printM('Writing channels: %s' % self.chans, self.sender)
		self.numchns = rs.numchns
		self.stime = 1/rs.sps
		self.inv = rs.inv

		printM('Starting.', self.sender)


	def getq(self):
		'''
		Reads data from the queue and updates the stream.

		:rtype: bool
		:return: Returns ``True`` if stream is updated, otherwise ``False``.
		'''
		d = self.queue.get(True, timeout=None)
		self.queue.task_done()
		if 'TERM' in str(d):
			self.alive = False
			printM('Exiting.', self.sender)
			sys.exit()
		elif str(d.decode('UTF-8')).split(' ')[0] in ['ALARM', 'RESET', 'IMGPATH']:
			pass
		else:
			if rs.getCHN(d) in self.chans:
				self.stream = rs.update_stream(
					stream=self.stream, d=d, fill_value=None)
				return True
			else:
				return False
	
	def set_sps(self):
		'''
		Sets samples per second.
		'''
		self.sps = self.stream[0].stats.sampling_rate

	def elapse(self, new=False):
		'''
		Ticks self variables over into a new day for file naming purposes.

		:param bool new: If ``False``, the program is starting. If ``True``, the UTC date just elapsed.
		'''
		self.st = UTCDateTime.now()
		self.y, self.m, self.d = self.st.year, self.st.month, self.st.day
		self.j = self.st.strftime('%j')
		self.newday = UTCDateTime(self.y, self.m, self.d, 0, 0) + timedelta(days=1.1)
		self.newday = UTCDateTime(self.newday.year, self.newday.month, self.newday.day, 0, 0)
		if new:
			self.last = self.newday
		else:
			self.last = self.st

	def slicestream(self):
		'''
		Causes the stream to slice down to the time the last write operation was made.
		'''
		self.stream.slice(starttime=self.last)

	def _tracewrite(self, t):
		'''
		Processing for the :py:func:`rsudp.c_write.Write.write` function.
		Writes an input trace to disk.

		:type t: obspy.core.trace.Trace
		:param t: The trace segment to write to disk.

		'''
		enc = 'STEIM2'	# encoding
		if isinstance(t.data, rs.np.ma.masked_array):
			t.data = t.data.filled(fill_value=0) # fill array (to avoid obspy write error)
		outfile = self.outdir + '/%s.%s.00.%s.D.%s.%s' % (t.stats.network,
							t.stats.station, t.stats.channel, self.y, self.j)
		if not outfile in self.outfiles:
			self.outfiles.append(outfile)
		if os.path.exists(os.path.abspath(outfile)):
			with open(outfile, 'ab') as fh:
				t.write(fh, format='MSEED', encoding=enc)
				if self.debug:
					printM('%s records to %s'
							% (len(t.data), outfile), self.sender)
		else:
			t.write(outfile, format='MSEED', encoding=enc)
			if self.debug:
				printM('%s records to new file %s'
						% (len(t.data), outfile), self.sender)


	def write(self, stream=False):
		'''
		Writes a segment of the stream to disk as miniSEED, and appends it to the
		file in question. If there is no file (i.e. if the program is just starting
		or a new UTC day has just started, then this function writes to a new file).

		:type stream: obspy.core.stream.Stream or bool
		:param stream: The stream segment to write. If ``False``, the program has just started.
		'''
		if not stream:
			self.last = self.stream[0].stats.endtime - timedelta(seconds=5)
			stream = self.stream.copy().slice(
						endtime=self.last, nearest_sample=False)

		for t in stream:
			self._tracewrite(t)
		if self.testing:
			TEST['c_write'][1] = True

	def run(self):
		"""
		Reads packets and coordinates write operations.
		"""
		self.elapse()

		self.getq()
		self.set_sps()
		self.getq()
		printM('miniSEED output directory: %s' % (self.outdir), self.sender)
		if self.inv:
			printM('Writing inventory file: %s/%s.%s.00.xml' % (self.outdir,
					self.stream[0].stats.network,
					self.stream[0].stats.station), self.sender)
			self.inv.write('%s/%s.%s.00.xml' % (self.outdir,
					self.stream[0].stats.network,
					self.stream[0].stats.station),
					format='STATIONXML')
		printM('Beginning miniSEED output.', self.sender)
		wait_pkts = (self.numchns * 10) / (rs.tf / 1000) 	# comes out to 10 seconds (tf is in ms)

		n = 0
		while True:
			while True:
				if self.queue.qsize() > 0:
					self.getq()
					time.sleep(0.01)		# wait a few ms to see if another packet will arrive
					n += 1
				else:
					self.getq()
					n += 1
					break
			if n >= wait_pkts:
				if self.newday < UTCDateTime.now(): # end of previous day and start of new day
					self.write(self.stream.slice(
								endtime=self.newday, nearest_sample=False))
					self.stream = self.stream.slice(
								starttime=self.newday, nearest_sample=False)
					self.elapse(new=True)
				else:
					self.write()
					self.stream = self.stream.slice(
								starttime=self.last, nearest_sample=False)
				self.stream = rs.copy(self.stream)
				n = 0

				self.getq()
				time.sleep(0.01)		# wait a few ms to see if another packet will arrive
			sys.stdout.flush()
			sys.stderr.flush()
