import sys
from threading import Thread
from rsudp import printM


class Consumer(Thread):
	def __init__(self, queue, destinations):
		"""
		Initialize the process
		"""
		super().__init__()

		self.sender = 'Consumer'
		printM('Starting.', self.sender)
		self.queue = queue
		self.destinations = destinations
		self.running = True

	def run(self):
		"""
		Distributes queue objects to execute various other tasks: for example,
		it may be used to populate ObsPy streams for various things like
		plotting, alert triggers, and ground motion calculation.
		"""
		try:
			while self.running:
				p = self.queue.get()
				self.queue.task_done()

				for q in self.destinations:
					q.put(p)

				if 'TERM' in str(p):
					printM('Exiting.', self.sender)
					sys.exit()
		except Exception as e:
			return e
