import sys, os
import signal
import getopt
import time
import json
import logging
from queue import Queue
from rsudp import printM, default_loc
import rsudp.raspberryshake as RS
from rsudp.c_consumer import Consumer
from rsudp.c_printraw import PrintRaw
from rsudp.c_write import Write
from rsudp.c_plot import Plot, mpl
from rsudp.c_forward import Forward
from rsudp.c_alert import Alert
import pkg_resources as pr
import fnmatch
try:
	from pydub import AudioSegment
	from pydub.playback import play
	pydub_exists = True
except ImportError:
	pydub_exists = False


def eqAlert(sound=False, sender='EQAlert function', *args, **kwargs):
	printM('Trigger threshold exceeded -- possible earthquake!', sender=sender)
	if sound and pydub_exists:
		play(sound)


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

	if settings['forward']['enabled']:
		# put settings in namespace
		addr = settings['forward']['address']
		port = settings['forward']['port']
		cha = settings['forward']['channels']
		# set up queue and process
		q = mk_q()
		forward = Forward(addr=addr, port=port, cha=cha, q=q)
		mk_p(forward)

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
		alertsound = settings['alert']['alertsound']

		if pydub_exists and alertsound:
			soundloc = os.path.expanduser(os.path.expanduser(settings['alert']['mp3file']))
			if 'rs_sounds' in soundloc:
				soundloc = pr.resource_filename('rsudp', soundloc)
			try:
				sound = AudioSegment.from_file(soundloc, format="mp3")
				printM('Loaded %.2f sec alert sound from %s' % (len(sound)/1000., soundloc), sender='Alert')
			except IndexError as e:#FileNotFoundError as e:
				if ['ffprobe' in str(e)] or ['avprobe' in str(e)]:
					printM("WARNING: You have chosen to play a sound, but don't have ffmpeg or libav installed.", sender='Alert')
					printM('         Sound playback requires one of these dependencies.', sender='Alert')
					printM("         To install either dependency, follow the instructions at:", sender='Alert')
					printM('         https://github.com/jiaaro/pydub#playback', sender='Alert')
					printM('         The program will now continue without sound playback.', sender='Alert')
				else:
					raise FileNotFoundError('MP3 file could not be found')
				sound = False
		elif [ not pydub_exists ] and [ alertsound ]:
			sound = False
			printM("WARNING: You don't have pydub installed, so no sound will play.", sender='Alert')
			printM('         To install pydub, follow the instructions at:', sender='Alert')
			printM('         https://github.com/jiaaro/pydub#installation', sender='Alert')
			printM('         Sound playback also requires you to install either ffmpeg or libav.', sender='Alert')
		else:
			pass

		# set up queue and process
		q = mk_q()
		alrt = Alert(sta=sta, lta=lta, thresh=thresh, reset=reset, bp=bp, func=ex,
					 cha=cha, win_ovr=win_ovr, debug=debug, q=q, sound=sound)
		mk_p(alrt)


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

def dump_default(settings_loc, default_settings):
	printM('Creating a default settings file at %s' % settings_loc, sender='Main')
	with open(settings_loc, 'w+') as f:
		f.write(default_settings)
		f.write('\n')


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
"forward": {
    "enabled": false,
    "address": "192.168.1.254",
    "port": 8888,
    "channels": ["all"]},
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
    "alertsound": false,
    "mp3file": "rs_sounds/doorbell.mp3",
    "win_override": false,
    "debug": false}
}
"""

	settings = json.loads(default_settings)
	settings_loc = os.path.join(default_loc, 'rsudp_settings.json')

	try:
		opts = getopt.getopt(sys.argv[1:], 'hds:',
			['help', 'dump', 'settings=']
			)[0]
	except Exception as e:
		printM('ERROR: %s' % e, sender='Main')
		print(hlp_txt)

	if len(opts) == 0:
		if not os.path.exists(settings_loc):
			printM('Could not find rsudp settings file, creating one at %s' % settings_loc, sender='Main')
			dump_default(settings_loc, default_settings)
		else:
			with open(os.path.abspath(settings_loc), 'r') as f:
				printM('Found default settings file: %s' % settings_loc)
				try:
					settings = json.load(f)
				except Exception as e:
					printM('ERROR:  Could not load default settings file.')
					printM('DETAIL: %s' % e)
					printM('        Either correct the file, or dump the overwrite the default settings file using the command:')
					printM('        shake_client -d default')
					exit(2)

	for o, a in opts:
		if o in ('-h, --help'):
			print(hlp_txt)
			exit(0)
		if o in ('-d', '--dump'):
			if a in 'default':
				os.makedirs(default_loc)
				dump_default(settings_loc, default_settings)
			print(default_settings)
			exit(0)
		if o in ('-s', 'settings='):
			if os.path.exists(os.path.abspath(os.path.expanduser(a))):
				with open(os.path.abspath(os.path.expanduser(a)), 'r') as f:
					printM('Found settings file: %s' % settings_loc)
					try:
						settings = json.load(f)
					except Exception as e:
						printM('ERROR:  Could not load settings file. Perhaps the JSON is malformed?')
						printM('DETAIL: %s' % e)
						printM('        If you would like to rebuild the file, you can enter the command below:')
						printM('shake_client -d %s' % a)
						exit(2)
			else:
				printM('ERROR: could not find the settings file you specified. Check the path and try again.')
				print()
				exit(2)


	run(settings)

if __name__ == '__main__':
	main()
