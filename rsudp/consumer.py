import sys
from threading import Thread
from queue import Queue
from rsudp import printM

qsize = 2048 					# max queue size
destinations = []				# list of queues to distribute to

class Consumer(Thread):
	def __init__(self):
		"""
		Initialize the process
		"""
		super().__init__()

		self.sender = 'Consumer'
		printM('Starting.', self.sender)
		self.queue = Queue(qsize)
		self.running = True

	def run(self):
		"""
		Distributes queue objects to execute various other tasks: for example,
		it may be used to populate ObsPy streams for various things like
		plotting, alert triggers, and ground motion calculation.
		"""
		global destinations
		try:
			while self.running:
				p = self.queue.get()
				self.queue.task_done()

				for q in destinations:
					q.put(p)

				if 'TERM' in str(p):
					sys.exit()
		except Exception as e:
			return e
