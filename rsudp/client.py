import sys, os
import signal
import getopt
import time
import json
import re
import logging
from queue import Queue
from rsudp import printM, default_loc, init_dirs, output_dir, add_debug_handler
import rsudp.raspberryshake as RS
from rsudp.c_consumer import Consumer
from rsudp.p_producer import Producer
from rsudp.c_printraw import PrintRaw
from rsudp.c_write import Write
from rsudp.c_plot import Plot, mpl
from rsudp.c_forward import Forward
from rsudp.c_alert import Alert
from rsudp.c_alertsound import AlertSound
from rsudp.c_tweet import Tweeter
import pkg_resources as pr
import fnmatch
try:
	from pydub import AudioSegment
	pydub_exists = True
except ImportError:
	pydub_exists = False


def eqAlert(sound=False, sender='EQAlert function', *args, **kwargs):
	printM('Trigger threshold exceeded -- possible earthquake!', sender=sender)

def handler(sig, frame):
	RS.producer = False

def run(settings, debug):

	# handler for the exit signal
	signal.signal(signal.SIGINT, handler)

	RS.initRSlib(dport=settings['settings']['port'],
				 rsstn=settings['settings']['station'])

	output_dir = settings['settings']['output_dir']

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
		# set up queue and process
		cha = settings['write']['channels']
		q = mk_q()
		writer = Write(q=q, cha=cha)
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
		kiosk = settings['plot']['kiosk']
		screencap = settings['plot']['eq_screenshots']
		alert = settings['alert']['enabled']
		if settings['plot']['deconvolve']:
			deconv = settings['plot']['units']
		else:
			deconv = False
		pq = mk_q()
		Plotter = Plot(cha=cha, seconds=sec, spectrogram=spec,
						fullscreen=full, kiosk=kiosk, deconv=deconv, q=pq,
						screencap=screencap, alert=alert)

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
		ex = eqAlert if settings['alert']['exec'] in 'eqAlert' else settings['alert']['exec']
		if settings['alert']['deconvolve']:
			deconv = settings['alert']['units']
		else:
			deconv = False

		# set up queue and process
		q = mk_q()
		alrt = Alert(sta=sta, lta=lta, thresh=thresh, reset=reset, bp=bp, func=ex,
					 cha=cha, win_ovr=win_ovr, debug=debug, q=q,
					 deconv=deconv)
		mk_p(alrt)

	if settings['alertsound']['enabled']:
		sender = 'AlertSound'
		sound = False
		if pydub_exists:
			soundloc = os.path.expanduser(os.path.expanduser(settings['alertsound']['mp3file']))
			if soundloc in ['doorbell', 'alarm', 'beeps', 'sonar']:
				soundloc = pr.resource_filename('rsudp', os.path.join('rs_sounds', '%s.mp3' % soundloc))
			try:
				sound = AudioSegment.from_file(soundloc, format="mp3")
				printM('Loaded %.2f sec alert sound from %s' % (len(sound)/1000., soundloc), sender='AlertSound')
			except FileNotFoundError as e:
				if ['ffprobe' in str(e)] or ['avprobe' in str(e)]:
					printM("WARNING: You have chosen to play a sound, but don't have ffmpeg or libav installed.", sender='AlertSound')
					printM('         Sound playback requires one of these dependencies.', sender='AlertSound')
					printM("         To install either dependency, follow the instructions at:", sender='AlertSound')
					printM('         https://github.com/jiaaro/pydub#playback', sender='AlertSound')
					printM('         The program will now continue without sound playback.', sender='AlertSound')
				else:
					raise FileNotFoundError('MP3 file could not be found')
				sound = False
		else:
			sound = False
			printM("WARNING: You don't have pydub installed, so no sound will play.", sender='AlertSound')
			printM('         To install pydub, follow the instructions at:', sender='AlertSound')
			printM('         https://github.com/jiaaro/pydub#installation', sender='AlertSound')
			printM('         Sound playback also requires you to install either ffmpeg or libav.', sender='AlertSound')

		q = mk_q()
		alsnd = AlertSound(q=q, sound=sound)
		mk_p(alsnd)

	if settings['tweets']['enabled']:
		consumer_key = settings['tweets']['api_key']
		consumer_secret = settings['tweets']['api_secret']
		access_token = settings['tweets']['access_token']
		access_token_secret = settings['tweets']['access_secret']
		tweet_images = settings['tweets']['tweet_images']

		q = mk_q()
		tweet = Tweeter(q=q, consumer_key=consumer_key, consumer_secret=consumer_secret,
						access_token=access_token, access_token_secret=access_token_secret,
						tweet_images=tweet_images)
		mk_p(tweet)


	# master queue and consumer
	queue = Queue(RS.qsize)
	cons = Consumer(queue, destinations)
	cons.start()

	for thread in threads:
		thread.start()

	prod = Producer(queue, threads)
	prod.start()

	if settings['plot']['enabled'] and mpl:
		Plotter.master_queue = queue
		Plotter.run()
	else:
		while not prod.stop:
			time.sleep(0.1)


	time.sleep(0.5)

	print()
	printM('Shutdown successful.', 'Main')
	sys.exit()

def dump_default(settings_loc, default_settings):
	print('Creating a default settings file at %s' % settings_loc)
	with open(settings_loc, 'w+') as f:
		f.write(default_settings)
		f.write('\n')


def main():
	'''
	Loads settings to start the main client.
	Supply -h to see help text.
	'''
	settings_loc = os.path.join(default_loc, 'rsudp_settings.json').replace('\\', '/')

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
##  - numpy, obspy, matplotlib 3, pydub  ##
##                                       ##
###########################################

Usage: rs-client [ OPTIONS ]
where OPTIONS := {
    -h | --help
            display this help message
    -d | --dump=default or /path/to/settings/json
            dump the default settings to a JSON-formatted file
    -s | --settings=/path/to/settings/json
            specify the path to a JSON-formatted settings file
    }

rs-client with no arguments will start the program with
settings in %s
''' % settings_loc

	def default_settings(output_dir='%s/rsudp' % os.path.expanduser('~').replace('\\', '/'), verbose=True):
		def_settings = r"""{
"settings": {
    "port": 8888,
    "station": "Z0000",
    "output_dir": "%s",
    "debug": true},
"printdata": {
    "enabled": false},
"write": {
    "enabled": false,
    "channels": ["all"]},
"plot": {
    "enabled": true,
    "duration": 30,
    "spectrogram": true,
    "fullscreen": false,
    "kiosk": false,
    "eq_screenshots": false,
    "channels": ["HZ", "HDF"],
    "deconvolve": false,
    "units": "CHAN"},
"forward": {
    "enabled": false,
    "address": "192.168.1.254",
    "port": 8888,
    "channels": ["all"]},
"alert": {
    "enabled": true,
    "highpass": 0,
    "lowpass": 50,
    "deconvolve": false,
    "units": "VEL",
    "sta": 6,
    "lta": 30,
    "threshold": 1.7,
    "reset": 1.6,
    "exec": "eqAlert",
    "channel": "HZ",
    "win_override": false},
"alertsound": {
    "enabled": false,
    "mp3file": "doorbell"},
"tweets": {
    "enabled": false,
    "tweet_images": true,
    "api_key": "n/a",
    "api_secret": "n/a",
    "access_token": "n/a",
    "access_secret": "n/a"}
}
""" % (output_dir)
		if verbose:
			print('By default output_dir is set to %s' % output_dir)
		return def_settings

	settings = json.loads(default_settings(verbose=False))

	# get arguments
	try:
		opts = getopt.getopt(sys.argv[1:], 'hid:s:',
			['help', 'install' 'dump=', 'settings=']
			)[0]
	except Exception as e:
		print('ERROR: %s' % e)
		print(hlp_txt)

	if len(opts) == 0:
		if not os.path.exists(settings_loc):
			print('Could not find rsudp settings file, creating one at %s' % settings_loc)
			dump_default(settings_loc, default_settings())
		else:
			with open(os.path.abspath(settings_loc), 'r') as f:
				try:
					data = f.read().replace('\\', '/')
					settings = json.loads(data)
				except Exception as e:
					printM('ERROR:  Could not load default settings file from %s' % settings_loc)
					printM('DETAIL: %s' % e)
					printM('        Either correct the file, or overwrite the default settings file using the command:')
					printM('        shake_client -d default')
					exit(2)

	for o, a in opts:
		if o in ('-h, --help'):
			print(hlp_txt)
			exit(0)
		if o in ('-i', '--install'):
			'''
			This is only meant to be used by the install script.
			'''
			os.makedirs(default_loc, exist_ok=True)
			dump_default(settings_loc, default_settings(output_dir='@@DIR@@', verbose=False))
			exit(0)
		if o in ('-d', '--dump='):
			'''
			Dump the settings to a file, specified after the `-d` flag, or `-d default` to let the software decide where to put it.
			'''
			if str(a) in 'default':
				os.makedirs(default_loc, exist_ok=True)
				dump_default(settings_loc, default_settings())
			else:
				dump_default(os.path.abspath(os.path.expanduser(a)), default_settings())
			exit(0)
		if o in ('-s', 'settings='):
			'''
			Start the program with a specific settings file, for example: `-s settings.json`.
			'''
			if os.path.exists(os.path.abspath(os.path.expanduser(a))):
				settings_loc = os.path.abspath(os.path.expanduser(a)).replace('\\', '/')
				with open(settings_loc, 'r') as f:
					try:
						data = f.read().replace('\\', '/')
						settings = json.loads(data)
					except Exception as e:
						print('ERROR:  Could not load settings file. Perhaps the JSON is malformed?')
						print('DETAIL: %s' % e)
						print('        If you would like to overwrite and rebuild the file, you can enter the command below:')
						print('shake_client -d %s' % a)
						exit(2)
			else:
				print('ERROR: could not find the settings file you specified. Check the path and try again.')
				print()
				exit(2)

	debug = settings['settings']['debug']
	if debug:
		add_debug_handler()
		printM('Logging initialized successfully.', sender='Main')

	printM('Using settings file: %s' % settings_loc)

	odir = os.path.abspath(os.path.expanduser(settings['settings']['output_dir']))
	init_dirs(odir)
	if debug:
		printM('Output directory is: %s' % odir)

	run(settings, debug=debug)

if __name__ == '__main__':
	main()
