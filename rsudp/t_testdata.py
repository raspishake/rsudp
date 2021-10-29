import os, sys
from threading import Thread
import socket as s
from rsudp import printM, printW, helpers
import rsudp.raspberryshake as rs
from rsudp.test import TEST
import time
from queue import Empty


class TestData(Thread):
	'''
	.. versionadded:: 0.4.3

	A simple module that reads lines formatted as Raspberry Shake UDP packets
	from a file on disk, and sends them to the specified localhost port.
	Designed to quit on seeing a ``TERM`` string as the last line of the file
	or when an ``ENDTEST`` packet arrives on this thread's queue.

	For a diagram of ``TestData``'s position in the data hierarchy, see
	:ref:`testing_flow`.

	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`
	:param str data_file: data file to read from disk
	:param port: network port to pass UDP data to (at ``localhost`` address)
	:type port: str or int
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

		printW('Sending test data from %s'
			   % self.data_file, sender=self.sender, announce=False)

	def send(self):
		'''
		Send the latest line in the open file to the specified port at localhost.
		If the next line's timestamp is the same,
		that line will also be sent immediately.
		If the next line does not contain the same timestamp,
		the program will seek back to the last line read
		and then break for a new loop.

		If the line contains ``TERM``, the program will set ``self.alive = False``
		and prepare to exit.
		'''
		l = self.f.readline()
		if ('TERM' in l.decode('utf-8')) or (l.decode('utf-8') == ''):
			printM('End of file.', self.sender)
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

	def _getq(self):
		'''
		Gets a data packet from the queue and returns it.
		If no packet is immediately available, an ``Empty`` exception
		will be raised.

		:return: a bytes-encoded queue message
		:rtype: bytes
		'''
		q = self.queue.get_nowait()
		self.queue.task_done()
		return q

	def run(self):
		'''
		Start the thread. First, opens a file, determines the speed of data flow,
		then opens a socket and begins sending data at that transmission rate.

		Continues sending data until an ``ENDTEST`` packet arrives on the queue,
		or until the reader reaches the end of the file.
		Then, sends a ``TERM`` message to the localhost port and exits.
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

		printW('Sending data to %s:%s every %s seconds'
			   % (self.addr, self.port, self.speed),
			   sender=self.sender, announce=False)

		while self.alive:
			try:
				q = self._getq()
				if q.decode('utf-8') in 'ENDTEST':
					self.alive = False
					break
			except Empty:
				self.send()
				time.sleep(self.speed)
				TEST['x_send'][1] = True

		self.f.close()
		self.sock.sendto(helpers.msg_term(), (self.addr, self.port))
		printW('Exiting.', self.sender, announce=False)
		sys.exit()
