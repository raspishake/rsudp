from threading import Thread
import time
import random
from queue import Queue
import rsudp.raspberryshake as RS


queue = Queue(16)

def start_listen(port):
	RS.initRSlib(dport=port)
	RS.openSOCK()


class ProducerThread(Thread):
	def run(self):
		"""
		Receives data from one IP address and puts it in an async queue.
		Prints each sending address to STDOUT so the user can troubleshoot.
		This will work best on local networks where a router does not obscure
		multiple devices behind one sending IP.
		Remember, UDP packets cannot be differentiated by sending instrument.
		Their identifiers are per channel (EHZ, HDF, ENE, SHZ, etc.)
		and not per Shake (R4989, R52CD, R24FA, RCB43, etc.). To avoid problems,
		please use a separate port for each Shake.
		"""
		global queue
		firstaddr = ''
		blocked = []
		while True:
			data, addr = RS.sock.recvfrom(4096)
			if firstaddr == '':
				firstaddr = addr[0]
				RS.printM('Receiving UDP data from %s' % (firstaddr))
			if (firstaddr != '') and (addr[0] == firstaddr):
				queue.put(data)
			else:
				if addr not in blocked:
					RS.printM('Another IP (%s) is sending UDP data to this port. Ignoring...' % (addr[0]))
					blocked.append(addr)


class ConsumerThread(Thread):
	def run(self):
		"""
		Distributes queue objects to execute various other tasks: for example,
		it may be used to populate ObsPy streams for various things like
		plotting, alert triggers, and ground motion calculation.
		"""
		global queue
		while True:
			p = queue.get()
			queue.task_done()
			print(p)

def main():
	start_listen(port=18001)
	prod = ProducerThread()
	cons = ConsumerThread()
	prod.start()
	cons.start()

if __name__ == '__main__':
	main()
