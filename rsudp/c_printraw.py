import sys
from rsudp.raspberryshake import ConsumerThread
from rsudp import printM, printW, printE
from rsudp.test import TEST


class PrintRaw(ConsumerThread):
	"""
	A sub-consumer class that simply prints incoming data to the terminal.
	This is enabled by setting the "printdata" > "enabled" parameter to `true`
	in the settings file. This is more of a debug feature than anything else,
	meant to be a way to check that data is flowing into the port as expected.

	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`
	"""

	def __init__(self, q=False, testing=False):
		"""
		Initializing the data printing process.

		"""
		super().__init__()
		self.sender = 'Print'
		self.alive = True
		self.testing = testing

		if q:
			self.queue = q
		else:
			printE('no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			self.alive = False
			sys.exit()

		printM('Starting.', self.sender)

	def run(self):
		"""
		Reads data from the queue and print to stdout.
		"""
		while True:
			d = self.queue.get()
			self.queue.task_done()
			if 'TERM' in str(d):
				self.alive = False
				printM('Exiting.', self.sender)
				sys.exit()
			elif 'ALARM' in str(d):
				pass
			else:
				if not self.testing:
					print(str(d))
				else:
					TEST['c_print'][1] = True
			sys.stdout.flush()

		self.alive = False