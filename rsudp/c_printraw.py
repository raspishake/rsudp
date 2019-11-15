import sys
from threading import Thread
from rsudp import printM


class PrintRaw(Thread):
	"""
	A sub-consumer class that simply prints incoming data to the terminal.
	This is enabled by setting the "printdata" > "enabled" parameter to `true`
	in the settings file. This is more of a debug feature than anything else,
	meant to be a way to check that data is flowing into the port as expected.


	"""

	def __init__(self, q=False):
		"""
		Initialize the process
		"""
		super().__init__()
		self.sender = 'Print'
		self.alarm = False
		self.alive = True

		if q:
			self.queue = q
		else:
			printM('ERROR: no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			self.alive = False
			sys.exit()

		printM('Starting.', self.sender)

	def run(self):
		"""
		Reads data from the queue and print to stdout
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
				print(str(d))
			sys.stdout.flush()

		self.alive = False