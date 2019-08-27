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



def main():
	#global alrtq
	port = 18001
	start_listen(port=port, sta='R3BCF')
	RS.test_connection()

	prod = RS.ProducerThread()
	cons = RS.ConsumerThread()

	alrt = RS.AlertThread()
	prnt = RS.PrintThread()
	#plot = RS.PlotThread()

	prod.start()
	cons.start()

	alrt.start()
	prnt.start()
	#plot.start()

if __name__ == '__main__':
	main()
