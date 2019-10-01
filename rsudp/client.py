import sys, os
import signal
import getopt
import time
import json
from queue import Queue
from rsudp import printM
import rsudp.raspberryshake as RS
from rsudp.c_consumer import Consumer
from rsudp.c_printraw import PrintRaw
from rsudp.c_alert import Alert
from rsudp.c_write import Write
from rsudp.c_plot import Plot, mpl


def eqAlert(sender='EQAlert function', *args, **kwargs):
	printM('Trigger threshold exceeded -- possible earthquake!', sender=sender)


def prod(queue, threads):
	sender = 'Producer'
	chns = []
	numchns = 0
	stop = False

	"""
	Receives data from one IP address and puts it in an async queue.
	Prints each sending address to STDOUT so the user can troubleshoot.
	This will work best on local networks where a router does not obscure
	multiple devices behind one sending IP.
	Remember, RS UDP packets cannot be differentiated by sending instrument.
	Their identifiers are per channel (EHZ, HDF, ENE, SHZ, etc.)
	and not per Shake (R4989, R52CD, R24FA, RCB43, etc.). To avoid problems,
	please use a separate port for each Shake.
	"""
	firstaddr = ''
	blocked = []
	RS.producer = True
	while RS.producer:
		data, addr = RS.sock.recvfrom(4096)
		if firstaddr == '':
			firstaddr = addr[0]
			printM('Receiving UDP data from %s' % (firstaddr), sender)
		if (firstaddr != '') and (addr[0] == firstaddr):
			queue.put(data)
		else:
			if addr[0] not in blocked:
				printM('Another IP (%s) is sending UDP data to this port. Ignoring...'
						% (addr[0]), sender)
				blocked.append(addr[0])
		for thread in threads:
			if not thread.alive:
				stop = True
		if stop:
			break
	
	print()
	printM('Sending TERM signal to threads...', sender)
	queue.put(b'TERM')
	queue.join()

def handler(sig, frame):
	RS.producer = False

def run(settings):

	# handler for the exit signal
	signal.signal(signal.SIGINT, handler)

	RS.initRSlib(dport=settings['settings']['port'],
				 rsstn=settings['settings']['station'])

	destinations, threads = [], []

	def mk_q():
		q = Queue(RS.qsize)
		destinations.append(q)
		return q
	def mk_p(proc):
		threads.append(proc)


	if settings['printdata']['enabled']:
		# set up queue and process
		q = mk_q()
		prnt = PrintRaw(q)
		mk_p(prnt)

	if settings['alert']['enabled']:
		# put settings in namespace
		sta = settings['alert']['sta']
		lta = settings['alert']['lta']
		thresh = settings['alert']['threshold']
		reset = settings['alert']['reset']
		bp = [settings['alert']['highpass'], settings['alert']['lowpass']]
		cha = settings['alert']['channel']
		win_ovr = settings['alert']['win_override']
		debug = settings['alert']['debug']
		ex = eqAlert if settings['alert']['exec'] in 'eqAlert' else settings['alert']['exec']
		# set up queue and process
		q = mk_q()
		alrt = Alert(sta=sta, lta=lta, thresh=thresh, reset=reset, bp=bp, func=ex,
					 cha=cha, win_ovr=win_ovr, debug=debug, q=q)
		mk_p(alrt)

	if settings['write']['enabled']:
		# put settings in namespace
		outdir = settings['write']['outdir']
		# set up queue and process
		q = mk_q()
		writer = Write(outdir=outdir, q=q)
		mk_p(writer)

	if settings['plot']['enabled'] and mpl:
		while True:
			if RS.numchns == 0:
				time.sleep(0.01)
				continue
			else:
				break
		cha = settings['plot']['channels']
		sec = settings['plot']['duration']
		spec = settings['plot']['spectrogram']
		full = settings['plot']['fullscreen']
		q = mk_q()
		plotter = Plot(cha=cha, seconds=sec, spectrogram=spec,
								fullscreen=full, q=q)
		mk_p(plotter)

	# master queue and consumer
	queue = Queue(RS.qsize)
	cons = Consumer(queue, destinations)
	cons.start()

	for thread in threads:
		thread.start()

	prod(queue, threads)

	time.sleep(0.5)
	print()
	printM('Shutdown successful.', 'Main')
	sys.exit()


def main():
	'''
	Loads port, station, network, and duration arguments to create a graph.
	Supply -p, -s, -n, and/or -d to change the port and the output plot
	parameters.
	'''

	hlp_txt='''
###########################################
##     R A S P B E R R Y  S H A K E      ##
##           UDP Data Library            ##
##            by Ian Nesbitt             ##
##            GNU GPLv3 2019             ##
##                                       ##
## Do various tasks with Shake data      ##
## like plot, trigger alerts, and write  ##
## to miniSEED.                          ##
##                                       ##
##  Requires:                            ##
##  - numpy, obspy, matplotlib v3        ##
##                                       ##
###########################################

Usage: rs-client [ OPTIONS ]
where OPTIONS := {
    -h | --help
            display this help message
    -d | --dump
            dump the default settings in a JSON-formatted string
    -s | --settings=/path/to/settings/json
            specify the path to a custom JSON-formatted settings file
    }

'''

	default_settings = """{
"settings": {
    "port": 8888,
    "station": "Z0000"},
"printdata": {
    "enabled": false},
"write": {
    "enabled": false,
    "outdir": "/home/pi",
    "channels": "all"},
"plot": {
    "enabled": true,
    "duration": 30,
    "spectrogram": false,
    "fullscreen": false,
    "channels": ["HZ", "HDF"]},
"alert": {
    "enabled": true,
    "sta": 6,
    "lta": 30,
    "threshold": 1.7,
    "reset": 1.6,
    "exec": "eqAlert",
    "highpass": 0,
    "lowpass": 50,
    "channel": "HZ",
    "win_override": false,
    "debug": false}
}
"""

	settings = json.loads(default_settings)

	opts = getopt.getopt(sys.argv[1:], 'hds:',
		['help', 'dump', 'settings=']
		)[0]
	for o, a in opts:
		if o in ('-h, --help'):
			print(hlp_txt)
			exit(0)
		if o in ('-d', '--dump'):
			print(default_settings)
			exit(0)
		if o in ('-s', 'settings='):
			if os.path.exists(os.path.abspath(a)):
				with open(os.path.abspath(a), 'r') as f:
					settings = json.load(f)
			else:
				print('ERROR: could not find the settings file you specified. Check the path and try again')
				print()
				exit(2)

	run(settings)

if __name__ == '__main__':
	main()
