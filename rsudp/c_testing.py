import sys, os
from threading import Thread
import rsudp.raspberryshake as rs
from rsudp import printM, printW

class Testing(Thread):
	'''
	.. versionadded:: 0.4.3

	'''
	def __init__(self, test, threads, q=False):
		"""
		Initializes the custom code execution thread.
		"""
		super().__init__()
		self.sender = 'Testing'
		self.alive = True
		self.alarm = False			# don't touch this
		self.alarm_reset = False	# don't touch this
		self.queue = q

		self.test = test
		self.chans = False
		self.threads = threads

		printW('Starting test.', sender=self.sender, announce=False)

	def run(self):
		if rs.inv:
			self.test['n_inventory'][1] = True

		while True:
			d = self.queue.get()
			self.queue.task_done()
			if 'TERM' in str(d):
				printM('Got TERM message...', sender=self.sender)
				self.test['c_TERM'][1] = True
				self.alive = False
				break
			elif 'ALARM' in str(d):
				printM('Got ALARM message...', sender=self.sender)
				self.test['c_ALARM'][1] = True
			elif 'RESET' in str(d):
				printM('Got RESET message...', sender=self.sender)
				self.test['c_RESET'][1] = True
			elif 'IMGPATH' in str(d):
				printM('Got IMGPATH message...', sender=self.sender)
				self.test['c_IMGPATH'][1] = True
			else:
				self.test['n_port'][1] = True
				self.test['c_data'][1] = True

		printW('Exiting.', sender=self.sender, announce=False)

		self.alive = False
		sys.exit()
