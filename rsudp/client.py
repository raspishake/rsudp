import sys, os
import signal
import getopt
import time
import json
import traceback
from queue import Queue
from rsudp import printM, printW, printE, default_loc, init_dirs, settings_loc, add_debug_handler, start_logging
from rsudp import COLOR
import rsudp.helpers as H
import rsudp.test as T
import rsudp.raspberryshake as rs
from rsudp.packetize import packetize
from rsudp.c_consumer import Consumer
from rsudp.p_producer import Producer
from rsudp.c_printraw import PrintRaw
from rsudp.c_write import Write
from rsudp.c_plot import Plot, MPL
from rsudp.c_forward import Forward
from rsudp.c_alert import Alert
from rsudp.c_alertsound import AlertSound
from rsudp.c_custom import Custom
from rsudp.c_tweet import Tweeter
from rsudp.c_telegram import Telegrammer
from rsudp.c_rsam import RSAM
from rsudp.c_testing import Testing
from rsudp.t_testdata import TestData
import pkg_resources as pr


DESTINATIONS, THREADS = [], []
PROD = False
PLOTTER = False
TELEGRAM = False
TWITTER = False
WRITER = False
SOUND = False
TESTING = False
TESTQUEUE = False
TESTFILE = pr.resource_filename('rsudp', os.path.join('test', 'testdata'))
SENDER = 'Main'

def handler(sig, frame):
	'''
	Function passed to :py:func:`signal.signal` to handle close events
	'''
	rs.producer = False

def _xit(code=0):
	'''
	End the program. Called after all running threads have stopped.

	:param int code: The process code to exit with. 0=OK, 1=ERROR.
	'''
	if TESTING:
		TESTQUEUE.put(b'ENDTEST')
	for thread in THREADS:
		del thread
	
	printM('Shutdown successful.', sender=SENDER)
	print()
	sys.exit(code)

def test_mode(mode=None):
	'''
	Sets the TESTING global variable to ``True`` to indicate that
	testing-specific actions should be taken in routines.

	:param bool mode: if ``True`` or ``False``, sets testing mode state. if anything else, returns state only.
	:return: testing mode state
	:rtype: bool
	'''
	global TESTING
	if (mode == True) or (mode == False):
		TESTING = mode
	return TESTING


def mk_q():
	'''
	Makes a queue and appends it to the :py:data:`destinations`
	variable to be passed to the master consumer thread
	:py:class:`rsudp.c_consumer.Consumer`.

	:rtype: queue.Queue
	:return: Returns the queue to pass to the sub-consumer.
	'''
	q = Queue(rs.qsize)
	DESTINATIONS.append(q)
	return q

def mk_p(proc):
	'''
	Appends a process to the list of threads to start and stop.

	:param threading.Thread proc: The process thread to append to the list of threads.
	'''
	THREADS.append(proc)


def start():
	'''
	Start Consumer, Threads, and Producer.
	'''
	global PROD, PLOTTER, THREADS, DESTINATIONS
	# master queue and consumer
	queue = Queue(rs.qsize)
	cons = Consumer(queue, DESTINATIONS, testing=TESTING)
	cons.start()

	for thread in THREADS:
		thread.start()

	PROD = Producer(queue, THREADS, testing=TESTING)
	PROD.start()

	if PLOTTER and MPL:
		# give the plotter the master queue
		# so that it can issue a TERM signal if closed
		PLOTTER.master_queue = queue
		# start plotting (in this thread, not a separate one)
		PLOTTER.run()
	else:
		while not PROD.stop:
			time.sleep(0.1) # wait until processes end


	time.sleep(0.5) # give threads time to exit
	PROD.stop = True


def run(settings, debug):
	'''
	Main setup function. Takes configuration values and passes them to
	the appropriate threads and functions.

	:param dict settings: settings dictionary (see :ref:`defaults` for guidance)
	:param bool debug: whether or not to show debug output (should be turned off if starting as daemon)
	'''
	global PLOTTER, SOUND
	# handler for the exit signal
	signal.signal(signal.SIGINT, handler)

	if TESTING:
		global TESTQUEUE
		# initialize the test data to read information from file and put it on the port
		TESTQUEUE = Queue()		# separate from client library because this is not downstream of the producer
		tdata = TestData(q=TESTQUEUE, data_file=TESTFILE, port=settings['settings']['port'])
		tdata.start()

	# initialize the central library
	rs.initRSlib(dport=settings['settings']['port'],
				 rsstn=settings['settings']['station'])

	H.conn_stats(TESTING)
	if TESTING:
		T.TEST['n_port'][1] = True	# port has been opened
		if rs.sps == 0:
			printE('There is already a Raspberry Shake sending data to this port.', sender=SENDER)
			printE('For testing, please change the port in your settings file to an unused one.',
					sender=SENDER, spaces=True)
			_xit(1)


	output_dir = settings['settings']['output_dir']


	if settings['printdata']['enabled']:
		# set up queue and process
		q = mk_q()
		prnt = PrintRaw(q, testing=TESTING)
		mk_p(prnt)

	if settings['write']['enabled']:
		global WRITER
		# set up queue and process
		cha = settings['write']['channels']
		q = mk_q()
		WRITER = Write(q=q, data_dir=output_dir,
					   cha=cha, testing=TESTING)
		mk_p(WRITER)

	if settings['plot']['enabled'] and MPL:
		while True:
			if rs.numchns == 0:
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
			if settings['plot']['units'].upper() in rs.UNITS:
				deconv = settings['plot']['units'].upper()
			else:
				deconv = 'CHAN'
		else:
			deconv = False
		pq = mk_q()
		PLOTTER = Plot(cha=cha, seconds=sec, spectrogram=spec,
						fullscreen=full, kiosk=kiosk, deconv=deconv, q=pq,
						screencap=screencap, alert=alert, testing=TESTING)
		# no mk_p() here because the plotter must be controlled by the main thread (this one)

	if settings['forward']['enabled']:
		# put settings in namespace
		addr = settings['forward']['address']
		port = settings['forward']['port']
		cha = settings['forward']['channels']
		fwd_data = settings['forward']['fwd_data']
		fwd_alarms = settings['forward']['fwd_alarms']
		# set up queue and process
		if len(addr) == len(port):
			printM('Initializing %s Forward threads' % (len(addr)), sender=SENDER)
			for i in range(len(addr)):
				q = mk_q()
				forward = Forward(num=i, addr=addr[i], port=int(port[i]), cha=cha,
								  fwd_data=fwd_data, fwd_alarms=fwd_alarms,
								  q=q, testing=TESTING)
				mk_p(forward)
		else:
			printE('List length mismatch: %s addresses and %s ports in forward section of settings file' % (
										len(addr), len(port)), sender=SENDER)
			_xit(1)

	if settings['alert']['enabled']:
		# put settings in namespace
		sta = settings['alert']['sta']
		lta = settings['alert']['lta']
		thresh = settings['alert']['threshold']
		reset = settings['alert']['reset']
		bp = [settings['alert']['highpass'], settings['alert']['lowpass']]
		cha = settings['alert']['channel']
		if settings['alert']['deconvolve']:
			if settings['alert']['units'].upper() in rs.UNITS:
				deconv = settings['alert']['units'].upper()
			else:
				deconv = 'CHAN'
		else:
			deconv = False

		# set up queue and process
		q = mk_q()
		alrt = Alert(sta=sta, lta=lta, thresh=thresh, reset=reset, bp=bp,
					 cha=cha, debug=debug, q=q, testing=TESTING,
					 deconv=deconv)
		mk_p(alrt)

	if settings['alertsound']['enabled']:
		soundloc = os.path.expanduser(os.path.expanduser(settings['alertsound']['mp3file']))
		if soundloc in ['doorbell', 'alarm', 'beeps', 'sonar']:
			soundloc = pr.resource_filename('rsudp', os.path.join('rs_sounds', '%s.mp3' % soundloc))

		q = mk_q()
		alsnd = AlertSound(q=q, testing=TESTING, soundloc=soundloc)
		mk_p(alsnd)

	runcustom = False
	try:
		f = False
		win_ovr = False
		if settings['custom']['enabled']:
			# put settings in namespace
			f = settings['custom']['codefile']
			win_ovr = settings['custom']['win_override']
			if f == 'n/a':
				f = False
			runcustom = True
	except KeyError as e:
		if settings['alert']['exec'] != 'eqAlert':
			printW('the custom code function has moved to its own module (rsudp.c_custom)', sender='Custom')
			f = settings['alert']['exec']
			win_ovr = settings['alert']['win_override']
			runcustom = True
		else:
			raise KeyError(e)
	if runcustom:
		# set up queue and process
		q = mk_q()
		cstm = Custom(q=q, codefile=f, win_ovr=win_ovr, testing=TESTING)
		mk_p(cstm)


	if settings['tweets']['enabled']:
		global TWITTER
		consumer_key = settings['tweets']['api_key']
		consumer_secret = settings['tweets']['api_secret']
		access_token = settings['tweets']['access_token']
		access_token_secret = settings['tweets']['access_secret']
		tweet_images = settings['tweets']['tweet_images']
		extra_text = settings['tweets']['extra_text']

		q = mk_q()
		TWITTER = Tweeter(q=q, consumer_key=consumer_key, consumer_secret=consumer_secret,
						access_token=access_token, access_token_secret=access_token_secret,
						tweet_images=tweet_images, extra_text=extra_text, testing=TESTING)
		mk_p(TWITTER)

	if settings['telegram']['enabled']:
		global TELEGRAM
		token = settings['telegram']['token']
		chat_ids = settings['telegram']['chat_id'].strip(' ').split(',')
		send_images = settings['telegram']['send_images']
		extra_text = settings['telegram']['extra_text']

		for chat_id in chat_ids:
			sender = "Telegram id %s" % (chat_id)
			q = mk_q()
			TELEGRAM = Telegrammer(q=q, token=token, chat_id=chat_id,
								   send_images=send_images, extra_text=extra_text,
								   sender=sender, testing=TESTING)
			mk_p(TELEGRAM)

	if settings['rsam']['enabled']:
		# put settings in namespace
		fwaddr = settings['rsam']['fwaddr']
		fwport = settings['rsam']['fwport']
		fwformat = settings['rsam']['fwformat']
		interval = settings['rsam']['interval']
		cha = settings['rsam']['channel']
		quiet = settings['rsam']['quiet']
		if settings['rsam']['deconvolve']:
			if settings['rsam']['units'].upper() in rs.UNITS:
				deconv = settings['rsam']['units'].upper()
			else:
				deconv = 'CHAN'
		else:
			deconv = False

		# set up queue and process
		q = mk_q()
		rsam = RSAM(q=q, interval=interval, cha=cha, deconv=deconv,
					fwaddr=fwaddr, fwport=fwport, fwformat=fwformat,
					quiet=quiet, testing=TESTING)

		mk_p(rsam)


	# start additional modules here!
	################################


	################################

	if TESTING:
		# initialize test consumer
		q = mk_q()
		test = Testing(q=q)
		mk_p(test)


	# start the producer, consumer, and activated modules
	start()

	PLOTTER = False
	if not TESTING:
		_xit()
	else:
		printW('Client has exited, ending tests...', sender=SENDER, announce=False)


def main():
	'''
	Loads settings to start the main client.
	Supply -h from the command line to see help text.
	'''

	hlp_txt='''
###########################################
##     R A S P B E R R Y  S H A K E      ##
##              UDP Client               ##
##            by Ian Nesbitt             ##
##            GNU GPLv3 2020             ##
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


	settings = json.loads(H.default_settings(verbose=False))

	# get arguments
	try:
		opts = getopt.getopt(sys.argv[1:], 'hid:s:',
			['help', 'install', 'dump=', 'settings=']
			)[0]
	except Exception as e:
		print(COLOR['red'] + 'ERROR: %s' % e + COLOR['white'])
		print(hlp_txt)

	if len(opts) == 0:
		if not os.path.exists(settings_loc):
			print(COLOR['yellow'] + 'Could not find rsudp settings file, creating one at %s' % settings_loc + COLOR['white'])
			H.dump_default(settings_loc, H.default_settings())
		else:
			settings = H.read_settings(settings_loc)

	for o, a in opts:
		if o in ('-h', '--help'):
			print(hlp_txt)
			exit(0)
		if o in ('-i', '--install'):
			'''
			This is only meant to be used by the install script.
			'''
			os.makedirs(default_loc, exist_ok=True)
			H.dump_default(settings_loc, H.default_settings(output_dir='@@DIR@@', verbose=False))
			exit(0)
		if o in ('-d', '--dump='):
			'''
			Dump the settings to a file, specified after the `-d` flag, or `-d default` to let the software decide where to put it.
			'''
			if str(a) in 'default':
				os.makedirs(default_loc, exist_ok=True)
				H.dump_default(settings_loc, H.default_settings())
			else:
				H.dump_default(os.path.abspath(os.path.expanduser(a)), H.default_settings())
			exit(0)
		if o in ('-s', 'settings='):
			'''
			Start the program with a specific settings file, for example: `-s settings.json`.
			'''
			settings = H.read_settings(a)

	debug = settings['settings']['debug']
	if debug:
		add_debug_handler()
	start_logging()

	printM('Using settings file: %s' % settings_loc)

	odir = os.path.abspath(os.path.expanduser(settings['settings']['output_dir']))
	init_dirs(odir)
	if debug:
		printM('Output directory is: %s' % odir)

	run(settings, debug=debug)


def test():
	'''
	.. versionadded:: 0.4.3

	Set up tests, run modules, report test results.
	For a list of tests run, see :py:mod:`rsudp.test`.
	'''
	global TESTFILE
	hlp_txt='''
###########################################
##     R A S P B E R R Y  S H A K E      ##
##            Testing Module             ##
##            by Ian Nesbitt             ##
##            GNU GPLv3 2020             ##
##                                       ##
## Test settings with archived Shake     ##
## data to determine optimal             ##
## configuration.                        ##
##                                       ##
##  Requires:                            ##
##  - numpy, obspy, matplotlib 3         ##
##                                       ##
###########################################

Usage: rs-test [ OPTIONS ]
where OPTIONS := {
    -h | --help
            display this help message
    -f | --file=default or /path/to/data/file
            specify the path to a seismic data file
    -s | --settings=/path/to/settings/json
            specify the path to a JSON-formatted settings file
    -b | --no-plot
            "blind mode", used when there is no display
    -q | --no-sound
            "quiet mode", used when there is no audio device/ffmpeg
    }

rs-test with no arguments will start the test with
default settings and the data file at
%s
''' % (TESTFILE)

	test_mode(True)
	settings = H.default_settings(verbose=False)
	settings_are_default = True
	plot = True
	quiet = False
	customfile = False

	try:
		opts = getopt.getopt(sys.argv[1:], 'hf:s:bq',
			['help', 'file=', 'settings=', 'no-plot', 'no-sound']
			)[0]
	except Exception as e:
		print(COLOR['red'] + 'ERROR: %s' % e + COLOR['white'])
		print(hlp_txt)
		exit(1)

	for o, a in opts:
		# parse options and arguments
		if o in ('-h', '--help'):
			print(hlp_txt)
			exit(0)
		if o in ('-f', '--file='):
			'''
			The data file.
			'''
			a = os.path.expanduser(a)
			if os.path.exists(a):
				try:
					out = '%s.txt' % (a)
					packetize(inf=a, outf=out, testing=True)
					TESTFILE = out
					customfile = True # using a custom miniseed file for testing
				except Exception as e:
					print(hlp_txt)
					print(COLOR['red'] + 'ERROR: %s' % e + COLOR['white'])
					exit(1)
		if o in ('-s', '--settings='):
			'''
			Dump the settings to a file, specified after the `-d` flag, or `-d default` to let the software decide where to put it.
			'''
			settings_loc = os.path.abspath(os.path.expanduser(a)).replace('\\', '/')
			if os.path.exists(settings_loc):
				settings = H.read_settings(settings_loc)
				settings_are_default = False
			else:
				print(COLOR['red'] + 'ERROR: could not find settings file at %s' % (a) + COLOR['white'])
				exit(1)
		if o in ('-b', '--no-plot'):
			plot = False
		if o in ('-q', '--no-sound'):
			quiet = True

	if not customfile:
		# we are just using the default miniseed file
		packetize(inf=TESTFILE+'.ms', outf=TESTFILE, testing=True)

	T.TEST['n_internet'][1] = T.is_connected('www.google.com')

	if settings_are_default:
		settings = T.make_test_settings(settings=settings, inet=T.TEST['n_internet'][1])

	T.TEST['p_log_dir'][1] = T.logdir_permissions()
	T.TEST['p_log_file'][1] = start_logging(testing=True)
	T.TEST['p_log_std'][1] = add_debug_handler(testing=True)

	T.TEST['p_output_dirs'][1] = init_dirs(os.path.expanduser(settings['settings']['output_dir']))
	T.TEST['p_data_dir'][1] = T.datadir_permissions(os.path.expanduser(settings['settings']['output_dir']))
	T.TEST['p_screenshot_dir'][1] = T.ss_permissions(os.path.expanduser(settings['settings']['output_dir']))

	settings = T.cancel_tests(settings, MPL, plot, quiet)

	try:
		run(settings, debug=True)

		# client test
		ctest = 'client test'
		if (T.TEST['c_miniseed'] and WRITER):
			printM('Merging and testing MiniSEED file(s)...', sender=ctest)
			try:
				ms = rs.Stream()
				for outfile in WRITER.outfiles:
					if os.path.exists(outfile):
						T.TEST['c_miniseed'][1] = True
						ms = ms + rs.read(outfile)
						dn, fn = os.path.dirname(outfile), os.path.basename(outfile)
						os.replace(outfile, os.path.join(dn, 'test.' + fn))
					else:
						raise FileNotFoundError('MiniSEED file not found: %s' % outfile)
				printM('Renamed test file(s).', sender=ctest)
				printM(ms.merge().__str__())
			except Exception as e:
				printE(e)
				T.TEST['c_miniseed'][1] = False

	except Exception as e:
		printE(traceback.format_exc(), announce=False)
		printE('Ending tests.', sender=SENDER, announce=False)
		time.sleep(0.5)


	TESTQUEUE.put(b'ENDTEST')
	printW('Test finished.', sender=SENDER, announce=False)

	print()

	code = 0
	printM('Test results:')
	for i in T.TEST:
		printM('%s: %s' % (T.TEST[i][0], T.TRANS[T.TEST[i][1]]))
		if not T.TEST[i][1]:
			# if a test fails, change the system exit code to indicate an error occurred
			code = 1
	_xit(code)


if __name__ == '__main__':
	main()
