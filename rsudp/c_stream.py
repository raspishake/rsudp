import sys, time
from rsudp.raspberryshake import ConsumerThread
import rsudp.raspberryshake as rs
from rsudp import printM, printW, printE, helpers


class StreamBuilder(rs.ConsumerThread):
	"""
	A simple routine to write daily miniSEED data to :code:`output_dir/data`.

	:param cha: channel(s) to forward. others will be ignored.
	:type cha: str or list
	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`
	:param bool debug: whether or not to display messages when writing data to disk.
	"""
	def __init__(self, q, debug=False, cha='all'):
		"""
		Initialize the process
		"""
		super().__init__()
		self.sender = 'StreamBuilder'
		self.alive = True

		self.queue = q

		self.stream = rs.Stream()
		self.debug = debug

		self.chans = []
		helpers.set_channels(self, cha)

		printM('Building stream of channels: %s' % self.chans, self.sender)
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


	def run(self):
		"""
		"""
		self.getq()
		self.set_sps()
		while True:
			if self.queue.qsize() > 0:
				self.getq()
				time.sleep(0.01)		# wait a few ms to see if another packet will arrive
			else:
				self.getq()
