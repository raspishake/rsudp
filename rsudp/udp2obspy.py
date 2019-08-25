from threading import Thread
import time
import random
import signal
from queue import Queue
from obspy.core.trace import Trace
from obspy.core.stream import Stream
from obspy.core.utcdatetime import UTCDateTime
from obspy.signal.trigger import recursive_sta_lta
from obspy.signal.trigger import z_detect
from obspy import read_inventory
import numpy as np
import math
from obspy import UTCDateTime
from datetime import datetime, timedelta

import rsudp.raspberryshake as RS
import rsudp.rs2o as rso

inv = False

global drawq, alrtq, forwq
global destinations
drawq = Queue(RS.qsize)	# plot queue
alrtq = Queue(RS.qsize)	# alert queue
forwq = Queue(RS.qsize)	# forwarding queue


def start_listen(port, sta):
	RS.initRSlib(dport=port, rssta=sta)
	RS.openSOCK()

def get_inventory(sta='Z0000'):
	global inv
	if 'Z0000' in sta:
		RS.printM('No station name given, continuing without inventory.')
		inv = False
	else:
		try:
			RS.printM('Fetching inventory for station %s.%s from Raspberry Shake FDSN.' % (RS.net, RS.sta))
			inv = read_inventory('https://fdsnws.raspberryshakedata.com/fdsnws/station/1/query?network=%s&station=%s&level=resp&format=xml'
								 % (RS.net, RS.sta))
			RS.printM('Inventory fetch successful.')
		except:
			RS.printM('Inventory fetch failed, continuing without.')
			inv = False


class AlertThread(Thread):
	def run(self):
		"""

		"""
		global alrtq, inv
		alert_stream = Stream()
		sta='R3BCF'
		get_inventory(sta=sta)
		if inv:
			alert_stream.attach_response(inv)
		alert_stream.select(component='Z')

		tf = 4
		n = 0
		sta = 5
		lta = 10

		wait_pkts = tf * lta
		while True:
			while True:
				d = RS.destinations['alerts'].get()
				RS.destinations['alerts'].task_done()
				alert_stream = rso.update_stream(
					stream=alert_stream, d=d, fill_value='latest')
				df = alert_stream[0].stats.sampling_rate
				break

			if n > (lta * tf):
				obstart = alert_stream[0].stats.endtime - timedelta(seconds=lta)	# obspy time
				alert_stream = alert_stream.slice(starttime=obstart)	# slice the stream to the specified length (seconds variable)

				cft = recursive_sta_lta(alert_stream[0], int(sta * df), int(lta * df))
				if cft.max() > 1.4:
				#cft = z_detect(alert_stream[0], int(sta * df))
				#if cft.max() > 1.1:
					RS.printM('Event detected! CFT: %s (waiting %s for clear trigger)' % (cft.max(), lta))
					n = 1
				#else:
				#	RS.printM('                     CFT: %s' % (cft.max()))
			elif n == 0:
				RS.printM('Earthquake trigger warmup time of %s seconds...' % (lta))
				n += 1
			elif n == (tf * lta):
				RS.printM('Earthquake trigger up and running normally.')
				n += 1
			else:
				n += 1




def main():
	global alrtq
	port = 18001
	start_listen(port=port, sta='R3BCF')
	RS.test_connection()

	prod = RS.ProducerThread()
	cons = RS.ConsumerThread()

	if True:
		alrt = AlertThread()
		#draw = DrawThread()
		#forw = ForwardThread()
		RS.destinations['alerts'] = alrtq#, drawq, forwq]

	prod.start()
	cons.start()

	alrt.start()

if __name__ == '__main__':
	main()
