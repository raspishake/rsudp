import os, sys
import socket as s
from threading import Thread
from rsudp import printM
import rsudp.raspberryshake as RS

class Forward(Thread):
	def __init__(self, addr, port, cha, q):
		"""
		Initialize the process
		"""
		super().__init__()

		self.sender = 'Forward'
		printM('Starting.', self.sender)
		self.queue = q
		self.addr = addr
		self.port = port
		self.chans = []
		cha = RS.chns if (cha == 'all') else cha
		cha = list(cha) if isinstance(cha, str) else cha
		l = RS.chns
		for c in l:
			n = 0
			for uch in cha:
				if (uch.upper() in c) and (c not in str(self.chans)):
					self.chans.append(c)
				n += 1
		if len(self.chans) < 1:
			self.chans = RS.chns
		self.alarm = False
		self.running = True
		self.alive = True

	def run(self):
		"""
		Distributes queue objects to another address and port on the network.
		"""
		printM('Opening socket...', sender=self.sender)
		socket_type = s.SOCK_DGRAM if os.name in 'nt' else s.SOCK_DGRAM | s.SO_REUSEADDR
		sock = s.socket(s.AF_INET, socket_type)

		printM('Forwarding %s data to %s:%s' % (self.chans, self.addr, self.port), sender=self.sender)

		try:
			while self.running:
				p = self.queue.get()	# get a packet
				self.queue.task_done()	# close the queue

				if 'TERM' in str(p):	# shutdown if there's a TERM message on the queue
					self.alive = False
					printM('Exiting.', self.sender)
					sys.exit()

				if RS.getCHN(p) in self.chans:
					sock.sendto(p, (self.addr, self.port))

		except Exception as e:
			self.alive = False
			printM('ERROR: %s' % e, sender=self.sender)
			sys.exit(2)

