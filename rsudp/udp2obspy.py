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
		global queue
		firstaddr = ''
		notif = False
		while True:
			data, addr = RS.sock.recvfrom(4096)
			if firstaddr == '':
				firstaddr = addr[0]
				RS.printM('Receiving UDP data from %s' % (firstaddr))
			if (firstaddr != '') and (addr[0] == firstaddr):
				queue.put(data)
			else:
				if notif == False:
					RS.printM('Another address (%s) is sending UDP data to this port. Ignoring...' % (addr[0]))
					notif = True


class ConsumerThread(Thread):
	def run(self):
		global queue
		while True:
			p = queue.get()
			queue.task_done()
			print(p)

def main():
	try:
		start_listen(port=18001)
		prod = ProducerThread()
		cons = ConsumerThread()
		prod.start()
		cons.start()
	except KeyboardInterrupt:
		RS.printM('Output ended.')

if __name__ == '__main__':
	main()
