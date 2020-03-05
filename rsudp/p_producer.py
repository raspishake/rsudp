import sys
from threading import Thread
from rsudp import printM, printW, printE
import rsudp.raspberryshake as RS


class Producer(Thread):
	'''
	Data Producer thread (see :ref:`producer-consumer`) which receives data from the port
	and puts it on the queue to be passed to the master consumer (:py:class:`rsudp.c_consumer.Consumer`).
	The producer also looks for flags in each consumer
	that indicate whether they are ``alive==False``. If so, the Producer will
	quit gracefully and put a TERM message on the queue, which should stop all running
	consumers.

	:param queue.Queue queue: The master queue, used to pass data to :py:class:`rsudp.c_consumer.Consumer`
	:param list threads: The list of :py:class:`threading.Thread` s to monitor for status changes
	'''

	def __init__(self, queue, threads):
		"""
		Initializing Producer thread. 
		
		"""
		super().__init__()

		self.sender = 'Producer'
		self.queue = queue
		self.threads = threads
		self.stop = False

		self.firstaddr = ''
		self.blocked = []

		printM('Starting.', self.sender)

	def run(self):
		"""
		Distributes queue objects to execute various other tasks: for example,
		it may be used to populate ObsPy streams for various things like
		plotting, alert triggers, and ground motion calculation.
		"""
		RS.producer = True
		while RS.producer:
			data, addr = RS.sock.recvfrom(4096)
			if self.firstaddr == '':
				self.firstaddr = addr[0]
				printM('Receiving UDP data from %s' % (self.firstaddr), self.sender)
			if (self.firstaddr != '') and (addr[0] == self.firstaddr):
				self.queue.put(data)
				if data.decode('utf-8') == 'TERM':
					RS.producer = False
					self.stop = True
			else:
				if addr[0] not in self.blocked:
					printM('Another IP (%s) is sending UDP data to this port. Ignoring...'
							% (addr[0]), self.sender)
					self.blocked.append(addr[0])
			for thread in self.threads:
				if thread.alarm:
					self.queue.put(b'ALARM %s' % bytes(str(RS.UTCDateTime.now()), 'utf-8'))
					printM('%s thread has indicated alarm state, sending ALARM message to queues'
						   % thread.sender, sender=self.sender)
					thread.alarm = False
				if thread.alarm_reset:
					self.queue.put(b'RESET %s' % bytes(str(RS.UTCDateTime.now()), 'utf-8'))
					printM('%s thread has indicated alarm reset, sending RESET message to queues'
						   % thread.sender, sender=self.sender)
					thread.alarm_reset = False
				if not thread.alive:
					self.stop = True
			if self.stop:
				RS.producer = False
				break

		print()
		printM('Sending TERM signal to threads...', self.sender)
		self.queue.put(b'TERM')
		self.stop = True
		sys.exit()
