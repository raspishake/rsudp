from threading import Thread
import rsudp.raspberryshake as rs
from rsudp import printM

class Testing(Thread):
	'''
	.. versionadded:: 0.4.3

	'''
	def __init__(self, test, threads, q=False):
		"""
		Initializes the custom code execution thread.
		"""
		super().__init__()
		self.sender = 'Custom'
		self.alive = True
		self.alarm = False			# don't touch this
		self.alarm_reset = False	# don't touch this
		self.queue = q

		self.test = test
		self.threads = threads

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
				printM('Exiting.', self.sender)
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


		self.alive = False