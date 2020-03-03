import sys
from threading import Thread
from rsudp import printM, printW, printE


class Consumer(Thread):
	"""
	The main consumer process. This consumer reads
	queue messages from the :class:`rsudp.p_producer.Producer`
	and distributes those messages to each sub-consumer in ``destinations``.

	:param queue.Queue queue: queue of data and messages sent by :class:`rsudp.p_producer.Producer`
	:param list destinations: list of :py:class:`queue.Queue` objects to pass data to
	"""


	def __init__(self, queue, destinations):
		"""
		Initializes the main consumer. 
		
		"""
		super().__init__()

		self.sender = 'Consumer'
		self.queue = queue
		self.destinations = destinations
		self.running = True

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
		except Exception as e:
			return e

		sys.exit()
