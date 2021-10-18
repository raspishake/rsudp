import sys
from threading import Thread
from rsudp import printM, printW, printE
from rsudp.test import TEST


class Consumer(Thread):
	"""
	The main consumer process. This consumer reads
	queue messages from the :class:`rsudp.p_producer.Producer`
	and distributes those messages to each sub-consumer in ``destinations``.

	:param queue.Queue queue: queue of data and messages sent by :class:`rsudp.p_producer.Producer`
	:param list destinations: list of :py:class:`queue.Queue` objects to pass data to
	"""


	def __init__(self, queue, destinations, testing=False):
		"""
		Initializes the main consumer. 
		
		"""
		super().__init__()

		self.sender = 'Consumer'
		self.queue = queue
		self.destinations = destinations
		self.running = True
		self.testing = testing

		printM('Starting.', self.sender)

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
					break

				if self.testing:
					TEST['x_masterqueue'][1] = True

		except Exception as e:
			return e

		sys.exit()
