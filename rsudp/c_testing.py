import sys, os
from threading import Thread
import rsudp.raspberryshake as rs
from rsudp import printM, printW
import rsudp.test as t

class Testing(Thread):
	'''
	.. versionadded:: 0.4.3

	'''
	def __init__(self, q):
		"""
		Initializes the custom code execution thread.
		"""
		super().__init__()
		self.sender = 'Testing'
		self.alive = True
		self.alarm = False			# don't touch this
		self.alarm_reset = False	# don't touch this
		self.queue = q

		self.stream = rs.Stream()
		self.cha = rs.chns

		printW('Starting test.', sender=self.sender, announce=False)

	def _getq(self):
		'''
		Reads data from the queue and updates the stream.

		:rtype: bool
		:return: Returns ``True`` if stream is updated, otherwise ``False``.
		'''
		d = self.queue.get(True, timeout=None)
		self.queue.task_done()
		return d

	def _getd(self):
		'''
		Reads data from the queue and updates the stream.

		:rtype: bool
		:return: Returns ``True`` if stream is updated, otherwise ``False``.
		'''
		d = self._getq()

		if rs.getCHN(d) in self.cha:
			self.stream = rs.update_stream(stream=self.stream, d=d, fill_value='latest')
		else:
			self._messagetests(d)

	def _datatests(self, d):
		'''

		'''

		if rs.getCHN(d) in self.cha:
			t.TEST['c_data'][1] = True
			self.stream = rs.update_stream(stream=self.stream, d=d, fill_value='latest')
			t.TEST['c_processing'][1] = True

	def _messagetests(self, d):
		'''

		'''
		if 'TERM' in str(d):
			printM('Got TERM message...', sender=self.sender)
			t.TEST['c_TERM'][1] = True
			self.alive = False
	
		elif 'ALARM' in str(d):
			printM('Got ALARM message...', sender=self.sender)
			t.TEST['c_ALARM'][1] = True

		elif 'RESET' in str(d):
			printM('Got RESET message...', sender=self.sender)
			t.TEST['c_RESET'][1] = True

		elif 'IMGPATH' in str(d):
			printM('Got IMGPATH message...', sender=self.sender)
			t.TEST['c_IMGPATH'][1] = True


	def run(self):
		'''

		'''
		if rs.inv:
			t.TEST['n_inventory'][1] = True
		self._datatests(self._getq())


		while self.alive:
			self._getd()

		t.TEST = t.TEST
		printW('Exiting.', sender=self.sender, announce=False)
		sys.exit()
