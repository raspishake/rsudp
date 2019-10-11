import os
import logging
from time import gmtime

default_loc = os.path.join(os.path.expanduser('~'), '.config', 'rsudp')
if not os.path.exists(default_loc):
	os.makedirs(default_loc)

logging.Formatter.converter = gmtime
f = logging.FileHandler(os.path.join(default_loc, 'rsudp.log'))
s = logging.StreamHandler()
logging.basicConfig(format='%(asctime)-15s %(msg)s', datefmt='%Y-%m-%d %H:%M:%S', handlers=[f,s])

def printM(msg, sender=''):
	'''Prints messages with datetime stamp.'''
	msg = '[%s] %s' % (sender, msg) if sender != '' else msg
	logging.critical(msg)
