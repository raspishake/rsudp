import sys
from threading import Thread
from rsudp import printM, printW, printE, helpers
import rsudp.raspberryshake as RS
from rsudp.test import TEST


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

	def __init__(self, queue, threads, testing=False):
		"""
		Initializing Producer thread. 
		
		"""
		super().__init__()

		self.sender = 'Producer'
		self.queue = queue
		self.threads = threads
		self.stop = False
		self.testing = testing

		self.firstaddr = ''
		self.blocked = []

		printM('Starting.', self.sender)


	def _filter_sender(self, data, addr):
		'''
		Filter the message sender and put data on the consumer queue.
		'''
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


	def _tasks(self):
		'''
		Execute tasks based on the states of sub-consumers.
		'''
		for thread in self.threads:
			# for each thread here
			if thread.alarm:
				# if there is an alarm in a sub thread, send the ALARM message to the queues
				self.queue.put(helpers.msg_alarm(thread.alarm))
				printM('%s thread has indicated alarm state, sending ALARM message to queues'
						% thread.sender, sender=self.sender)
				# now re-arm the trigger
				thread.alarm = False
			if thread.alarm_reset:
				# if there's an alarm_reset flag in a sub thread, send a RESET message
				self.queue.put(helpers.msg_reset(thread.alarm_reset))
				printM('%s thread has indicated alarm reset, sending RESET message to queues'
						% thread.sender, sender=self.sender)
				# re-arm the trigger
				thread.alarm_reset = False
			if not thread.alive:
				# if a thread stops, set the stop flag
				self.stop = True


	def run(self):
		"""
		Distributes queue objects to execute various other tasks: for example,
		it may be used to populate ObsPy streams for various things like
		plotting, alert triggers, and ground motion calculation.
		"""
		RS.producer = True
		while RS.producer:
			data, addr = RS.sock.recvfrom(4096)
			self._filter_sender(data, addr)
			self._tasks()
			if self.stop:
				RS.producer = False
				break
			if self.testing:
				TEST['x_data'][1] = True

		print()
		printM('Sending TERM signal to threads...', self.sender)
		self.queue.put(helpers.msg_term())
		self.stop = True
		sys.exit()
