import os, sys
import socket as s
from rsudp import printM, printW, printE
import rsudp.raspberryshake as rs
from rsudp.test import TEST

class Forward(rs.ConsumerThread):
	"""
	Single-destination data forwarding module. This consumer reads
	queue messages from the :class:`rsudp.c_consumer.Consumer`
	and forwards those messages to a specified address and port.
	Multiple of these threads can be started in order to deliver to
	more than one destination. (see the :ref:`datacast-forwarding`
	section in :doc:`settings`)

	.. versionadded:: 1.0.2

		The option to choose whether to forward either data or alarms or both
		(find boolean settings :code:`"fwd_data"` and :code:`"fwd_alarms"` in
		settings json files built by this version and later).

	:param str addr: IP address to pass UDP data to
	:param str port: network port to pass UDP data to (at specified address)
	:param bool fwd_data: whether or not to forward raw data packets
	:param bool fwd_alarms: whether or not to forward :code:`ALARM` and :code:`RESET` messages
	:param cha: channel(s) to forward. others will be ignored.
	:type cha: str or list
	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`
	"""

	def __init__(self, num, addr, port, fwd_data, fwd_alarms, cha, q, testing=False):
		"""
		Initializes data forwarding module.
		
		"""
		super().__init__()

		self.sender = 'Forward #%s (%s:%s)' % (num, addr, port)
		self.queue = q
		self.testing = testing
		self.addr = addr
		self.port = port
		self.fwd_data = fwd_data
		self.fwd_alarms = fwd_alarms
		self.chans = []
		cha = rs.chns if (cha == 'all') else cha
		cha = list(cha) if isinstance(cha, str) else cha
		l = rs.chns
		for c in l:
			n = 0
			for uch in cha:
				if (uch.upper() in c) and (c not in str(self.chans)):
					self.chans.append(c)
				n += 1
		if len(self.chans) < 1:
			self.chans = rs.chns
		self.running = True
		self.alive = True

		printM('Starting.', self.sender)


	def _exit(self):
		"""
		Exits the thread.
		"""
		self.alive = False
		printM('Exiting.', self.sender)
		sys.exit()


	def run(self):
		"""
		Gets and distributes queue objects to another address and port on the network.
		"""
		printM('Opening socket...', sender=self.sender)
		socket_type = s.SOCK_DGRAM if os.name in 'nt' else s.SOCK_DGRAM | s.SO_REUSEADDR
		sock = s.socket(s.AF_INET, socket_type)

		msg_data = '%s data' % (self.chans) if self.fwd_data else ''
		msg_and = ' and ' if (self.fwd_data and self.fwd_alarms) else ''
		msg_alarms = 'ALARM / RESET messages' if self.fwd_alarms else ''

		printM('Forwarding %s%s%s to %s:%s' % (msg_data, msg_and, msg_alarms, self.addr,
											   self.port), sender=self.sender)

		try:
			while self.running:
				p = self.queue.get()	# get a packet
				self.queue.task_done()	# close the queue

				if 'TERM' in str(p):	# shutdown if there's a TERM message on the queue
					self._exit()

				if 'IMGPATH' in str(p):
					continue

				if ('ALARM' in str(p)) or ('RESET' in str(p)):
					if self.fwd_alarms:
						sock.sendto(p, (self.addr, self.port))
					continue

				if "{'" in str(p):
					if (self.fwd_data) and (rs.getCHN(p) in self.chans):
						sock.sendto(p, (self.addr, self.port))

				if self.testing:
					TEST['c_forward'][1] = True

		except Exception as e:
			self.alive = False
			printE('%s' % e, sender=self.sender)
			if self.testing:
				TEST['c_forward'][1] = False
			sys.exit(2)

