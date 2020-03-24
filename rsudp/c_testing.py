import sys, os
from rsudp.raspberryshake import ConsumerThread
import rsudp.raspberryshake as rs
from rsudp import printM, printW, helpers
import rsudp.test as t

class Testing(rs.ConsumerThread):
	'''
	.. versionadded:: 0.4.3

	This is the test consumer thread.
	It operates just like a normal consumer,
	but its only function is to run tests for data processing
	and message passing.

	For a diagram of ``TestData``'s position in the data hierarchy, see
	:ref:`testing_flow`.

	Currently it has the power to run 7 tests from
	:py:mod:`rsudp.test`:

	.. code-block:: python

		TEST['n_inventory']
		TEST['c_data']
		TEST['c_processing']
		TEST['c_TERM']
		TEST['c_ALARM']
		TEST['c_RESET']
		TEST['c_IMGPATH']

	These tests represent inventory fetch, data packet reception,
	stream processing, and the reception of the four current message types:
	``TERM``, ``ALARM``, ``RESET``, and ``IMGPATH``.

	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`
	'''
	def __init__(self, q):
		"""
		Initializes the custom code execution thread.
		"""
		super().__init__()
		self.sender = 'Testing'
		self.alive = True
		self.queue = q

		self.stream = rs.Stream()
		self.cha = rs.chns

		printW('Starting test consumer.', sender=self.sender, announce=False)

	def _getq(self):
		'''
		Reads data from the queue and returns the queue object.

		:rtype: bytes
		:return: The queue object.
		'''
		d = self.queue.get(True, timeout=None)
		self.queue.task_done()
		return d

	def _getd(self):
		'''
		Reads data from the queue and updates the stream.
		'''
		d = self._getq()

		if rs.getCHN(d) in self.cha:
			self.stream = rs.update_stream(stream=self.stream, d=d, fill_value='latest')
		else:
			self._messagetests(d)

	def _datatests(self, d):
		'''
		Run tests on a data packet to see if it can be processed into a stream object.
		If so, mark the data and processing tests passed.

		:param bytes d: a data packet from the queue

		'''

		if rs.getCHN(d) in self.cha:
			t.TEST['c_data'][1] = True
			self.stream = rs.update_stream(stream=self.stream, d=d, fill_value='latest')
			t.TEST['c_processing'][1] = True

	def _messagetests(self, d):
		'''
		Run tests on a message to see if a specific one has been passed.
		If so, mark the test passed.

		:param bytes d: a data packet from the queue

		'''
		if 'TERM' in str(d):
			printM('Got TERM message...', sender=self.sender)
			t.TEST['c_TERM'][1] = True
			self.alive = False
	
		elif 'ALARM' in str(d):
			printM('Got ALARM message with time %s' % (
				   helpers.fsec(helpers.get_msg_time(d))
				   ), sender=self.sender)
			t.TEST['c_ALARM'][1] = True

		elif 'RESET' in str(d):
			printM('Got RESET message with time %s' % (
				   helpers.fsec(helpers.get_msg_time(d))
				   ), sender=self.sender)
			t.TEST['c_RESET'][1] = True

		elif 'IMGPATH' in str(d):
			printM('Got IMGPATH message with time %s' % (
				   helpers.fsec(helpers.get_msg_time(d))
				   ), sender=self.sender)
			printM('and path %s' % (helpers.get_msg_path(d)), sender=self.sender)
			t.TEST['c_IMGPATH'][1] = True


	def run(self):
		'''
		Start the testing thread and run until ``self.alive == False``.

		'''
		if rs.inv:
			t.TEST['n_inventory'][1] = True
		self._datatests(self._getq())


		while self.alive:
			self._getd()

		printW('Exiting.', sender=self.sender, announce=False)
		sys.exit()
