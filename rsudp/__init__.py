import os, sys
import logging
import warnings
from time import gmtime

default_loc = '%s/.config/rsudp' % os.path.expanduser('~').replace('\\', '/')
os.makedirs(default_loc, exist_ok=True)
log_dir = os.path.abspath('/tmp/rsudp')
os.makedirs(log_dir, exist_ok=True)

output_dir = False
data_dir = False
scap_dir = False

handlers = []
logging.getLogger().setLevel(logging.INFO)
logging.Formatter.converter = gmtime
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
logformat = '%(asctime)-15s %(msg)s'                 
formatter = logging.Formatter(fmt=logformat, datefmt=TIME_FORMAT)               

def init_dirs(odir):
	global output_dir, data_dir, scap_dir
	output_dir = odir
	data_dir = os.path.join(odir, 'data')
	scap_dir = os.path.join(odir, 'screenshots')
	try:
		os.makedirs(odir, exist_ok=True)
		os.makedirs(data_dir, exist_ok=True)
		os.makedirs(scap_dir, exist_ok=True)
	except OSError as e:
		print('Error creating output directory structure. Are you sure you have permission to write to the output folder?')
		print('More info: %s' % e)
		exit(2)

def add_debug_handler():
	s = logging.StreamHandler(sys.stdout)
	s.setLevel('INFO')
	s.setFormatter(formatter)
	logging.getLogger().addHandler(s)

f = logging.FileHandler(os.path.join(log_dir, 'rsudp.log'))
f.setLevel('INFO')
f.setFormatter(formatter)
handlers.append(f)
logging.basicConfig(handlers=handlers)

warnings.filterwarnings('ignore', category=UserWarning, module='rsudp')
warnings.filterwarnings('ignore', category=FutureWarning, module='obspy')

def printM(msg, sender=''):
	'''Prints messages with datetime stamp.'''
	msg = '[%s] %s' % (sender, msg) if sender != '' else msg
	logging.info(msg)
