import os, sys
from rsudp import COLOR, printM, printW, printE
import socket
import json

SENDER = 'test.py'
TEST = {
	# permissions
	'p_log_dir':			['log directory               ', False],
	'p_log_std':			['stdout logging              ', False],
	'p_log_file':			['logging to file             ', False],
	'p_output_dirs':		['output directory structure  ', False],
	'p_screenshot_dir':		['screenshot directory        ', False],
	'p_data_dir':			['data directory              ', False],

	# network
	'n_port':				['port                        ', False],
	'n_internet':			['internet                    ', False],
	'n_inventory':			['inventory (RS FDSN server)  ', False],

	# core
	'x_packetize':			['packetizing data            ', False],
	'x_send':				['sending data                ', False],
	'x_data':				['receiving data              ', False],
	'x_masterqueue':		['master queue                ', False],
	'x_processing':			['processing data             ', False],
	'x_ALARM':				['ALARM message               ', False],
	'x_RESET':				['RESET message               ', False],
	'x_IMGPATH':			['IMGPATH message             ', False],
	'x_TERM':				['TERM message                ', False],

	# dependencies
	'd_pydub':				['pydub dependencies          ', False],
	'd_matplotlib':			['matplotlib backend          ', False],

	# consumers
	'c_plot':				['plot                        ', False],
	'c_write':				['miniSEED write              ', False],
	'c_miniseed':			['miniSEED data               ', False],
	'c_print':				['print data                  ', False],
	'c_alerton':			['alert trigger on            ', False],
	'c_alertoff':			['alert trigger off           ', False],
	'c_play':				['play sound                  ', False],
	'c_img':				['screenshot exists           ', False],
	'c_tweet':				['Twitter text message        ', False],
	'c_tweetimg':			['Twitter image message       ', False],
	'c_telegram':			['Telegram text message       ', False],
	'c_telegramimg':		['Telegram image              ', False],
	'c_forward':			['forwarding                  ', False],
	'c_rsam':				['RSAM transmission           ', False],
	'c_custom':				['custom code execution       ', False],
}

TRANS = {
	True: COLOR['green'] + 'PASS' + COLOR['white'],
	False: COLOR['red'] + 'FAIL' + COLOR['white']
}

PORT = 18888

def make_test_settings(settings, inet=False):
	'''
	Get the default settings and return settings for testing.

	The default settings are modified in the following way:

	======================================== ===================
	Setting                                  Value
	======================================== ===================
	 ``settings['settings']['station']``      ``'R24FA'``
	 ``settings['printdata']['enabled']``     ``True``
	 ``settings['alert']['threshold']``       ``2``
	 ``settings['alert']['reset']``           ``0.5``
	 ``settings['alert']['lowpass']``         ``9``
	 ``settings['alert']['highpass']``        ``0.8``
	 ``settings['plot']['channels']``         ``['all']``
	 ``settings['plot']['duration']``         ``60``
	 ``settings['plot']['deconvolve']``       ``True``
	 ``settings['plot']['units']``            ``'CHAN'``
	 ``settings['plot']['eq_screenshots']``   ``True``
	 ``settings['write']['enabled']``         ``True``
	 ``settings['write']['channels']``        ``['all']``
	 ``settings['tweets']['enabled']``        ``True``
	 ``settings['telegram']['enabled']``      ``True``
	 ``settings['alertsound']['enabled']``    ``True``
	 ``settings['rsam']['enabled']``          ``True``
	 ``settings['rsam']['debug']``            ``True``
	 ``settings['rsam']['interval']``         ``10``
	======================================== ===================

	.. note::

		If there is no internet connection detected, the station
		name will default to ``'Z0000'`` so that no time is wasted
		trying to download an inventory from the Raspberry Shake
		FDSN service.

	:param dict settings: settings dictionary (will be modified from :ref:`defaults`)
	:param bool inet: whether or not the internet test passed
	:rtype: dict
	:return: settings dictionary to test with
	'''
	settings = json.loads(settings)

	settings['settings']['port'] = PORT
	if inet:
		settings['settings']['station'] = 'R24FA'
	else:
		settings['settings']['station'] = 'Z0000'

	settings['printdata']['enabled'] = True

	settings['alert']['threshold'] = 2
	settings['alert']['reset'] = 0.5
	settings['alert']['lowpass'] = 9
	settings['alert']['highpass'] = 0.8

	settings['plot']['channels'] = ['all']
	settings['plot']['duration'] = 60
	settings['plot']['deconvolve'] = True
	settings['plot']['units'] = 'CHAN'
	settings['plot']['eq_screenshots'] = True

	settings['write']['enabled'] = True
	settings['write']['channels'] = ['all']

	settings['telegram']['enabled'] = True
	settings['tweets']['enabled'] = True

	settings['alertsound']['enabled'] = True

	settings['forward']['enabled'] = True

	settings['rsam']['enabled'] = True
	settings['rsam']['quiet'] = False
	settings['rsam']['interval'] = 10

	return settings


def cancel_tests(settings, MPL, plot, quiet):
	'''
	Cancel some tests if they don't need to be run.

	:param dict settings: the dictionary of settings for program execution
	:param bool plot: whether or not to plot (``False`` == no plot)
	:param bool quiet: whether or not to play sounds (``True`` == no sound)
	:rtype: dict
	:return: settings dictionary to test with
	'''
	global TEST

	if plot:
		if MPL:
			TEST['d_matplotlib'][1] = True
		else:
			printW('matplotlib backend failed to load')
	else:
		settings['plot']['enabled'] = False
		del TEST['d_matplotlib']
		del TEST['c_IMGPATH']
		del TEST['c_img']
		printM('Plot is disabled')

	if quiet:
		settings['alertsound']['enabled'] = False
		del TEST['d_pydub']
		printM('Alert sound is disabled')

	if not settings['custom']['enabled']:
		del TEST['c_custom']

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

