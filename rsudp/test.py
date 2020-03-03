import os, sys
from rsudp import default_loc, init_dirs, output_dir, start_logging, add_debug_handler
from rsudp import COLOR, printM, printW, printE, test_mode
test_mode(True)
import rsudp.client as client
from rsudp.c_testing import Testing
from rsudp.t_testdata import TestData
from queue import Queue
import socket
import json
import time
import pkg_resources as pr

TEST = {
	# permissions
	'p_log_dir':			['log directory               ', False],
	'p_log_file':			['logging to file             ', False],
	'p_log_std':			['logging stdout              ', False],
	'p_output_dirs':		['output directory structure  ', False],
	'p_screenshot_dir':		['screenshot directory        ', False],
	'p_data_dir':			['data directory              ', False],
	# network
	'n_port':				['port                        ', False],
	'n_internet':			['internet                    ', False],
	'n_inventory':			['inventory fetch             ', False],
	# dependencies
	'd_pydub':				['pydub dependencies          ', False],
	'd_matplotlib':			['matplotlib backend          ', False],

	# core
	'c_data':				['receiving data              ', False],
	'c_processing':			['processing data             ', False],
	'c_ALARM':				['ALARM message               ', False],
	'c_RESET':				['RESET message               ', False],
	'c_IMGPATH':			['IMGPATH message             ', False],
	'c_TERM':				['TERM message                ', False],
}

TRANS = {True: 'PASS', False: 'FAIL'}

PORT = 18888

def make_test_settings(inet=False):
	'''
	Get the default settings and return settings for testing.

	:rtype: dict
	:return: settings to test with
	'''
	settings = json.loads(client.default_settings())

	settings['settings']['port'] = 18888
	if settings['settings']['station'] == 'Z0000':
		if inet:
			settings['settings']['station'] = 'R3BCF'

	settings['alert']['threshold'] = 2
	settings['alert']['reset'] = 0.5
	settings['alert']['lowpass'] = 9
	settings['alert']['highpass'] = 0.8

	settings['plot']['deconvolve'] = True

	settings['alertsound']['enabled'] = True

	return settings

def permissions(dp):
	'''
	Test write permissions for the specified directory.

	:param str dp: the directory path to test permissions for
	:rtype: bool
	:return: if ``True``, the test was successful, ``False`` otherwise
	'''
	dp = os.path.join(dp, 'test')
	try:
		with open(dp, 'w') as f:
			f.write('testing\n')
		os.remove(dp)
		return True
	except Exception as e:
		printE(e)
		return False

def datadir_permissions(testdir):
	'''
	Test write permissions in the data directory (``./data`` by default)

	:param str testdir: The directory to test permissions for
	:rtype: bool
	:return: the output of :py:func:`rsudp.test.permissions`

	'''
	return permissions('%s/data/' % testdir)

def ss_permissions(testdir):
	'''
	Test write permissions in the screenshots directory (``./screenshots`` by default)

	:param str testdir: The directory to test permissions for
	:rtype: bool
	:return: the output of :py:func:`rsudp.test.permissions`

	'''
	return permissions('%s/screenshots/' % testdir)

def logdir_permissions(logdir='/tmp/rsudp'):
	'''
	Test write permissions in the log directory (``/tmp/rsudp`` by default)

	:param str logdir: The log directory to test permissions for
	:rtype: bool
	:return: the output of :py:func:`rsudp.test.permissions`
	'''
	return permissions(logdir)

def is_connected(hostname):
	'''
	Test for an internet connection. 

	:param str hostname: The hostname to test with
	:rtype: bool
	:return: ``True`` if connection is successful, ``False`` otherwise
	'''
	try:
		# see if we can resolve the host name -- tells us if there is
		# a DNS listening
		host = socket.gethostbyname(hostname)
		# connect to the host -- tells us if the host is actually
		# reachable
		s = socket.create_connection((host, 80), 2)
		s.close()
		return True
	except:
		pass
	return False

def main():
	'''
	Set up tests, run modules, report test results
	'''
	global TEST

	TEST['p_log_dir'][1] = logdir_permissions()
	TEST['p_log_file'][1] = start_logging()
	TEST['p_log_std'][1] = add_debug_handler()

	TEST['n_internet'][1] = is_connected('www.google.com')

	settings = make_test_settings(inet=TEST['n_internet'][1])

	TEST['p_output_dirs'][1] = init_dirs(os.path.expanduser(settings['settings']['output_dir']))
	TEST['p_data_dir'][1] = datadir_permissions(os.path.expanduser(settings['settings']['output_dir']))
	TEST['p_screenshot_dir'][1] = ss_permissions(os.path.expanduser(settings['settings']['output_dir']))

	if client.mpl:
		TEST['d_matplotlib'][1] = True
	else:
		printW('matplotlib backend failed to load')


	data = pr.resource_filename('rsudp', os.path.join('test', 'testdata'))

	# initialize the test data to read information from file and put it on the port
	p = Queue()		# separate from client library because this is a private queue
	tp = TestData(q=p, data_file=data, port=settings['settings']['port'])
	tp.start()

	# initialize standard modules
	client.run(settings=settings, debug=True)
	# initialize test consumer
	q = client.mk_q()
	test = Testing(q=q, threads=client.THREADS, test=TEST)
	client.mk_p(test)

	TEST['d_pydub'][1] = client.SOUND


	client.start(settings)

	while not client.PROD.stop:
		time.sleep(0.1)	# if plotting is down, wait until processes end

	del client.PLOTTER	# necessary, not sure why
	TEST = test.test

	# shut down the testing module
	tp.queue.put('ENDTEST')

	time.sleep(0.5) # give threads time to exit

	printM('Shutdown successful.', 'test.py')
	print()
	client._xit()






if __name__ == '__main__':
	main()
