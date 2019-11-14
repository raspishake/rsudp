import sys
from threading import Thread
from rsudp import printM
import rsudp.raspberryshake as RS


class Producer(Thread):
	def __init__(self, queue, threads):
		"""
		Initialize the process
		"""
		super().__init__()

		self.sender = 'Producer'
		printM('Starting.', self.sender)
		self.queue = queue
		self.threads = threads
		self.stop = False

		self.firstaddr = ''
		self.blocked = []

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
			else:
				if addr[0] not in self.blocked:
					printM('Another IP (%s) is sending UDP data to this port. Ignoring...'
							% (addr[0]), self.sender)
					self.blocked.append(addr[0])
			for thread in self.threads:
				if thread.alarm:
					self.queue.put(b'ALARM %s' % bytes(str(RS.UTCDateTime.now()), 'utf-8'))
					print()
					printM('%s thread has indicated alarm state, sending ALARM message to queues' % thread.sender, sender=self.sender)
					thread.alarm = False
				if not thread.alive:
					self.stop = True
			if self.stop:
				RS.producer = False
				break

		print()
		printM('Sending TERM signal to threads...', self.sender)
		self.queue.put(b'TERM')
		self.queue.join()
		self.stop = True