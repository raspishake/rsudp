import os, sys
from threading import Thread, Timer
import socket as s
from rsudp import printM, printW
import rsudp.raspberryshake as rs
import time
from queue import Empty


class TestData(Thread):
	'''

	'''
	def __init__(self, q, data_file, port):
		"""
		Initializes the data supplier thread.
		"""
		super().__init__()
		self.sender = 'TestData'
		self.data_file = data_file
		self.port = port
		self.addr = 'localhost'
		self.speed = 0
		self.pos = 0
		self.queue = q
		self.sock = False
		self.alive = True

		printW('Sending test data from %s' % self.data_file, sender=self.sender, announce=False)

	def send(self):
		'''

		'''
		l = self.f.readline()
		if ('TERM' in l.decode('utf-8')) or (l.decode('utf-8') == ''):
			self.sock.sendto(b'TERM', (self.addr, self.port))
			printM('End of file.', self.sender)
			self.f.close()
			self.alive = False
		else:
			ts = rs.getTIME(l)
			self.sock.sendto(l, (self.addr, self.port))

			while True:
				self.pos = self.f.tell()
				l = self.f.readline()
				if 'TERM' in l.decode('utf-8'):
					break
				if rs.getTIME(l) == ts:
					self.sock.sendto(l, (self.addr, self.port))
				else:
					self.f.seek(self.pos)
					break


	def run(self):
		'''

		'''
		self.f = open(self.data_file, 'rb')
		self.f.seek(0)
		l = self.f.readline()
		l2 = self.f.readline()
		while (rs.getTIME(l2) == rs.getTIME(l)):
			l2 = self.f.readline()

		self.f.seek(0)

		self.speed = rs.getTIME(l2) - rs.getTIME(l)

		printW('Opening test socket...', sender=self.sender, announce=False)
		socket_type = s.SOCK_DGRAM if os.name in 'nt' else s.SOCK_DGRAM | s.SO_REUSEADDR
		self.sock = s.socket(s.AF_INET, socket_type)

		printW('Sending data to %s:%s every %s seconds' % (self.addr, self.port, self.speed),
			   sender=self.sender, announce=False)

		while True:
			try:
				q = self.queue.get_nowait()
				self.queue.task_done()
				printW('Exiting.', self.sender, announce=False)
				break
			except Empty:
				if self.alive:
					self.send()
				time.sleep(self.speed)

		self.alive = False
		sys.exit()
