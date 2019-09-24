import sys
from threading import Thread
from queue import Queue
from rsudp.c_consumer import destinations
from rsudp.raspberryshake import qsize
from rsudp import printM


class PrintRaw(Thread):
	"""
	A sub-consumer class that simply prints incoming data to the terminal.
	This is enabled by setting the "printdata" > "enabled" parameter to `true`
	in the settings file. This is more of a debug feature than anything else,
	meant to be a way to check that data is flowing into the port.


	"""

	def __init__(self):
		"""
		Initialize the process
		"""
		super().__init__()
		global destinations

		prntq = Queue(qsize)
		destinations.append(prntq)
		self.qno = len(destinations) - 1
		self.sender = 'Print'
		printM('Starting.', self.sender)

	def run(self):
		"""
		Reads data from the queue and print to stdout
		"""
		while True:
			d = destinations[self.qno].get()
			destinations[self.qno].task_done()
			if 'TERM' in str(d):
				sys.exit()
			print(str(d))
			sys.stdout.flush()
