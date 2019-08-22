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
		while True:
			r = RS.getDATA()
			queue.put(r)


class ConsumerThread(Thread):
	def run(self):
		global queue
		while True:
			p = queue.get()
			queue.task_done()
			print(p)

try:
	start_listen(port=18001)
	prod = ProducerThread()
	cons = ConsumerThread()
	prod.start()
	cons.start()
except KeyboardInterrupt:
	RS.printM('Output ended.')
