import os, sys
import logging
from time import gmtime
from . import _version

# saved in case needed in the future
# warnings.filterwarnings('ignore', category=UserWarning, module='rsudp')
# warnings.filterwarnings('ignore', category=FutureWarning, module='obspy')


'''
Contains logging and formatting resources for command line and logfile output of rsudp.
'''

name = 'rsudp'
__version__ = _version.version

default_loc = '%s/.config/rsudp' % os.path.expanduser('~').replace('\\', '/')
settings_loc = os.path.join(default_loc, 'rsudp_settings.json').replace('\\', '/')
os.makedirs(default_loc, exist_ok=True)
log_dir = os.path.abspath('/tmp/rsudp')
log_name = 'rsudp.log'
log_loc = os.path.join(log_dir, log_name)
os.makedirs(log_dir, exist_ok=True)

# formatter settings
logging.Formatter.converter = gmtime
LOG = logging.getLogger('main')
LOGFORMAT = '%(asctime)-15s %(msg)s'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

output_dir = False
data_dir = False
scap_dir = False
ms_path = False

COLOR = {
	'purple': '\033[95m',
	'blue': '\033[94m',
	'green': '\033[92m',
	'yellow': '\033[93m',
	'red': '\033[91m',
	'white': '\033[0m',
	'bold': "\033[1m"
}


def make_colors_friendly():
	'''
	Makes colors Windows-friendly if necessary.
	'''
	global COLOR
	if os.name == 'posix':
		pass	# terminal colors will work in this case
	else:
		for color in COLOR:
			COLOR[color] = ''

make_colors_friendly()


class LevelFormatter(logging.Formatter):
	'''
	.. |so_lf| raw:: html

		<a href="https://stackoverflow.com/a/28636024" target="_blank">this stackoverflow answer</a>

	A class that formats messages differently depending on their level.
	Adapted from |so_lf|.

	:param fmt: Format of message strings (see :py:mod:`logging`; example: ``'%(asctime)-15s %(msg)s'``)
	:type fmt: str or None
	:param datefmt: Date strings in strftime format (see :py:mod:`logging` example: ``'%Y-%m-%d %H:%M:%S'``)
	:type datefmt: str or None
	:param level_fmts: Dictionary of log levels and associated formats ``{logging.INFO: 'infoformat', logging.WARNING: 'warnformat', logging.ERROR: 'errformat'}``
	:type level_fmts: dict

	'''

	def __init__(self, fmt=None, datefmt=None, level_fmts={}):
		self._level_formatters = {}
		for level, format in level_fmts.items():
			# Could optionally support level names too
			self._level_formatters[level] = logging.Formatter(fmt=format, datefmt=datefmt)
		# self._fmt will be the default format
		super(LevelFormatter, self).__init__(fmt=fmt, datefmt=datefmt)
	# format records
	def format(self, record):
		if record.levelno in self._level_formatters:
			return self._level_formatters[record.levelno].format(record)
		return super(LevelFormatter, self).format(record)


def init_dirs(odir):
	'''
	Initialize the write directories if they do not already exist.

	:param str odir: output directory
	:return: ``True``
	:rtype: bool
	'''
	global output_dir, data_dir, scap_dir
	output_dir = odir
	data_dir = os.path.join(odir, 'data')
	scap_dir = os.path.join(odir, 'screenshots')
	try:
		os.makedirs(odir, exist_ok=True)
		os.makedirs(data_dir, exist_ok=True)
		os.makedirs(scap_dir, exist_ok=True)
	except OSError as e:
		print(COLOR['red'] + 'Error creating output directory structure. Are you sure you have permission to write to the output folder?' + COLOR['white'])
		print(COLOR['red'] + 'More info: %s' + COLOR['white'] % e)
		exit(2)

	return True


def start_logging(log_name=log_name, testing=False):
	'''
	Creates a handler for logging info and warnings to file.

	:param bool testing: whether or not testing is active (adds a "TESTING" label to messages)
	:return: ``True``
	:rtype: bool
	'''

	global LOG, LOGFORMAT
	LOG.setLevel('INFO')
	# logging formatters
	
	if testing:
		LOGFORMAT = '%(asctime)-15s TESTING %(msg)s'

	formatter = logging.Formatter(fmt=LOGFORMAT, datefmt=TIME_FORMAT)

	# this initializes logging to file
	f = logging.FileHandler(os.path.join(log_dir, log_name))
	f.setLevel('INFO')
	f.setFormatter(formatter)
	# warnings also go to file
	# initialize logging
	LOG.addHandler(f)
	printM('Logging initialized successfully.', sender='Init')
	return True


def add_debug_handler(testing=False):
	'''
	Creates an additional handler for logging info and warnings to the command line.

	:param bool testing: whether or not testing is active (adds a "TESTING" label to messages)
	:return: ``True``
	:rtype: bool
	'''
	global LOGFORMAT

	if testing:
		LOGFORMAT = '%(asctime)-15s TESTING %(msg)s'

	# terminal formats
	termformat = '\x1b[2K\r' + LOGFORMAT		# note '\x1b[2K' erases current line and \r returns to home
	# warning format
	warnformat = '\x1b[2K\r' + COLOR['yellow'] + LOGFORMAT + COLOR['white']
	# error format
	failformat = '\x1b[2K\r' + COLOR['red'] + LOGFORMAT + COLOR['white']
	termformatter = LevelFormatter(fmt=LOGFORMAT,
								   datefmt=TIME_FORMAT,
								   level_fmts={logging.INFO: termformat,
											   logging.WARNING: warnformat,
											   logging.ERROR: failformat},)
	s = logging.StreamHandler(sys.stdout)
	s.setLevel('INFO')
	s.setFormatter(termformatter)
	logging.getLogger('main').addHandler(s)
	return True


def get_scap_dir():
	'''
	This function returns the screen capture directory from the init function.
	This allows the variable to be more threadsafe.

	.. code-block:: python

		>>> get_scap_dir()
		'/home/pi/rsudp/screenshots/'

	:return: the path of the screenshot directory
	'''
	return scap_dir


def printM(msg, sender='', announce=False):
	'''
	Prints messages with datetime stamp and sends their output to the logging handlers.

	:param str msg: message to log
	:param str sender: the name of the class or function sending the message
	'''
	msg = u'[%s] %s' % (sender, msg) if sender != '' else msg
	# strip emoji from unicode by converting to ascii
	msg = msg.encode('ascii', 'ignore').decode('ascii')
	LOG.info(msg)


def printW(msg, sender='', announce=True, spaces=False):
	'''
	Prints warnings with datetime stamp and sends their output to the logging handlers.

	:param str msg: message to log
	:param str sender: the name of the class or function sending the message
	:param bool announce: whether or not to display "WARNING" before the message
	:param bool spaces: whether or not to display formatting spaces before the message
	'''
	if spaces:
		announce = False

	if announce:
		msg = u'[%s] WARNING: %s' % (sender, msg) if sender != '' else msg
	else:
		if spaces:
			msg = u'[%s]          %s' % (sender, msg) if sender != '' else msg
		else:
			msg = u'[%s] %s' % (sender, msg) if sender != '' else msg
	# strip emoji from unicode by converting to ascii
	msg = msg.encode('ascii', 'ignore').decode('ascii')
	LOG.warning(msg)


def printE(msg, sender='', announce=True, spaces=False):
	'''
	Prints errors with datetime stamp and sends their output to the logging handlers.

	:param str msg: message to log
	:param str sender: the name of the class or function sending the message
	:param bool announce: whether or not to display "WARNING" before the message
	:param bool spaces: whether or not to display formatting spaces before the message
	'''
	if spaces:
		announce = False

	if announce:
		msg = u'[%s] ERROR: %s' % (sender, msg) if sender != '' else msg
	else:
		if spaces:
			msg = u'[%s]        %s' % (sender, msg) if sender != '' else msg
		else:
			msg = u'[%s] %s' % (sender, msg) if sender != '' else msg
	# strip emoji from unicode by converting to ascii
	msg = msg.encode('ascii', 'ignore').decode('ascii')
	LOG.error(msg)
