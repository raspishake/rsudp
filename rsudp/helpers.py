import rsudp.raspberryshake as rs
from rsudp import COLOR, printM, printW, printE
import os
import json

from obspy.signal.util import _npts2nfft
from scipy.signal import resample
from scipy import integrate
from obspy.signal.filter import bandpass
import numpy as np

def dump_default(settings_loc, default_settings):
	'''
	Dumps a default settings file to a specified location.

	:param str settings_loc: The location to create the new settings JSON.
	:param str default_settings: The default settings to dump to file.
	'''
	print('Creating a default settings file at %s' % settings_loc)
	with open(settings_loc, 'w+') as f:
		f.write(default_settings)
		f.write('\n')


def default_settings(output_dir='%s/rsudp' % os.path.expanduser('~').replace('\\', '/'), verbose=True):
	'''
	Returns a formatted json string of default settings.

	:param str output_dir: the user's specified output location. defaults to ``~/rsudp``.
	:param bool verbose: if ``True``, displays some information as the string is created.
	:return: default settings string in formatted json
	:rtype: str
	'''
	def_settings = r"""
{
		"settings": {
				"port": 18888,
				"station": "Z0000",
				"output_dir": "%s",
				"debug": true
		},
		"printdata": {
				"enabled": false
		},
		"write": {
				"enabled": false,
				"channels": ["all"]
		},
		"plot": {
				"enabled": true,
				"duration": 90,
				"spectrogram": true,
				"fullscreen": false,
				"kiosk": false,
				"eq_screenshots": false,
				"channels": ["all"],
				"deconvolve": true,
				"units": "CHAN"
		},
		"forward": {
				"enabled": false,
				"address": ["192.168.1.254"],
				"port": [8888],
				"channels": ["all"],
				"fwd_data": true,
				"fwd_alarms": false
		},
		"alert": {
				"enabled": true,
				"channel": "HZ",
				"sta": 6,
				"lta": 30,
				"threshold": 3.95,
				"reset": 0.9,
				"highpass": 0.8,
				"lowpass": 9,
				"deconvolve": false,
				"units": "VEL"
		},
		"alertsound": {
				"enabled": false,
				"mp3file": "doorbell",
				"gtts_enabled": true
		},
		"custom": {
				"enabled": false,
				"codefile": "n/a",
				"win_override": false
		},
		"tweets": {
				"enabled": false,
				"tweet_images": true,
				"api_key": "n/a",
				"api_secret": "n/a",
				"access_token": "n/a",
				"access_secret": "n/a",
				"extra_text": ""
		},
		"telegram": {
				"enabled": false,
				"send_images": true,
				"token": "n/a",
				"chat_id": "n/a",
				"extra_text": ""
		},
		"rsam": {
				"enabled": false,
				"quiet": true,
				"fwaddr": "192.168.1.254",
				"fwport": 8887,
				"fwformat": "LITE",
				"channel": "HZ",
				"interval": 10,
				"deconvolve": false,
				"units": "VEL"
		},
		"process": {
			"enabled": true,
			"output_dir": "%s"
		},
		"dialog": {
			"enabled": true,
			"floor_num": 1,
			"disp_thresh": 0.5,
			"drift_thresh": 0.7,
			"autoclose": true
		}
}
""" % (output_dir, output_dir)

	if verbose:
		print('By default output_dir is set to %s' % output_dir)
	return def_settings


def read_settings(loc):
	'''
	Reads settings from a specific location.

	:param str loc: location on disk to read json settings file from
	:return: settings dictionary read from JSON, or ``None``
	:rtype: dict or NoneType
	'''
	settings_loc = os.path.abspath(os.path.expanduser(loc)).replace('\\', '/')
	settings = None
	with open(settings_loc, 'r') as f:
		try:
			data = f.read().replace('\\', '/')
			settings = json.loads(data)
		except Exception as e:
			print(COLOR['red'] + 'ERROR: Could not load settings file. Perhaps the JSON is malformed?' + COLOR['white'])
			print(COLOR['red'] + '			 detail: %s' % e + COLOR['white'])
			print(COLOR['red'] + '			 If you would like to overwrite and rebuild the file, you can enter the command below:' + COLOR['white'])
			print(COLOR['bold'] + '			 shake_client -d %s' % loc + COLOR['white'])
			exit(2)
	return settings


def set_channels(self, cha):
	'''
	This function sets the channels available for plotting. Allowed units are as follows:

	- ``["SHZ", "EHZ", "EHN", "EHE"]`` - velocity channels
	- ``["ENZ", "ENN", "ENE"]`` - acceleration channels
	- ``["HDF"]`` - pressure transducer channel
	- ``["all"]`` - all available channels

	So for example, if you wanted to display the two vertical channels of a Shake 4D,
	(geophone and vertical accelerometer) you could specify:

	``["EHZ", "ENZ"]``

	You can also specify partial channel names.
	So for example, the following will display at least one channel from any
	Raspberry Shake instrument:

	``["HZ", "HDF"]``

	Or if you wanted to display only vertical channels from a RS4D,
	you could specify

	``["Z"]``

	which would match both ``"EHZ"`` and ``"ENZ"``.

	:param self self: self object of the class calling this function
	:param cha: the channel or list of channels to plot
	:type cha: list or str
	'''
	cha = rs.chns if ('all' in cha) else cha
	cha = list(cha) if isinstance(cha, str) else cha
	for c in rs.chns:
		n = 0
		for uch in cha:
			if (uch.upper() in c) and (c not in str(self.chans)):
				self.chans.append(c)
			n += 1
	if len(self.chans) < 1:
			self.chans = rs.chns


def fsec(ti):
	'''
	.. versionadded:: 0.4.3

	The Raspberry Shake records at hundredths-of-a-second precision.
	In order to report time at this precision, we need to do some time-fu.

	This function rounds the microsecond fraction of a
	:py:class:`obspy.core.utcdatetime.UTCDateTime`
	depending on its precision, so that it accurately reflects the Raspberry Shake's
	event measurement precision.

	This is necessary because datetime objects in Python are strange and confusing, and
	strftime doesn't support fractional returns, only the full integer microsecond field
	which is an integer right-padded with zeroes. This function uses the ``precision``
	of a datetime object.

	For example:

	.. code-block:: python

		>>> from obspy import UTCDateTime
		>>> ti = UTCDateTime(2020, 1, 1, 0, 0, 0, 599000, precision=3)
		>>> fsec(ti)
		UTCDateTime(2020, 1, 1, 0, 0, 0, 600000)

	:param ti: time object to convert microseconds for
	:type ti: obspy.core.utcdatetime.UTCDateTime
	:return: the hundredth-of-a-second rounded version of the time object passed (precision is 0.01 second)
	:rtype: obspy.core.utcdatetime.UTCDateTime
	'''
	# time in python is weird and confusing, but luckily obspy is better than Python
	# at dealing with datetimes. all we need to do is tell it what precision we want
	# and it handles the rounding for us.
	return rs.UTCDateTime(ti, precision=2)


def lesser_multiple(x, base=10):
	'''
	.. versionadded:: 1.0.3

	This function calculates the nearest multiple of the base number ``base``
	for the number ``x`` passed to it, as long as the result is less than ``x``.

	This is useful for :func:`rsudp.packetize` when figuring out where to cut
	off samples when trying to fit them into packets.
	'''
	return int(base * int(float(x)/base))


def conn_stats(TESTING=False):
	'''
	Print some stats about the connection.

	Example:

	.. code-block:: python

		>>> conn_stats()
		2020-03-25 01:35:04 [conn_stats] Initialization stats:
		2020-03-25 01:35:04 [conn_stats]								 Port: 18069
		2020-03-25 01:35:04 [conn_stats]	 Sending IP address: 192.168.0.4
		2020-03-25 01:35:04 [conn_stats]		 Set station name: R24FA
		2020-03-25 01:35:04 [conn_stats]	 Number of channels: 4
		2020-03-25 01:35:04 [conn_stats]	 Transmission freq.: 250 ms/packet
		2020-03-25 01:35:04 [conn_stats]		Transmission rate: 4 packets/sec
		2020-03-25 01:35:04 [conn_stats]	 Samples per second: 100 sps
		2020-03-25 01:35:04 [conn_stats]						Inventory: AM.R24FA (Raspberry Shake Citizen Science Station)

	:param bool TESTING: if ``True``, text is printed to the console in yellow. if not, in white.
	'''
	s = 'conn_stats'
	pf = printW if TESTING else printM
	pf('Initialization stats:', sender=s, announce=False)
	pf('								Port: %s' % rs.port, sender=s, announce=False)
	pf('	Sending IP address: %s' % rs.firstaddr, sender=s, announce=False)
	pf('		Set station name: %s' % rs.stn, sender=s, announce=False)
	pf('	Number of channels: %s' % rs.numchns, sender=s, announce=False)
	pf('	Transmission freq.: %s ms/packet' % rs.tf, sender=s, announce=False)
	pf('	 Transmission rate: %s packets/sec' % rs.tr, sender=s, announce=False)
	pf('	Samples per second: %s sps' % rs.sps, sender=s, announce=False)
	if rs.inv:
		pf('					 Inventory: %s' % rs.inv.get_contents()['stations'][0],
				 sender=s, announce=False)


def msg_alarm(event_time):
	'''
	This function constructs the ``ALARM`` message as a bytes object.
	Currently this is only used by :py:class:`rsudp.p_producer.Producer`
	to construct alarm queue messages.

	For example:

	.. code-block:: python

		>>> from obspy import UTCDateTime
		>>> ti = UTCDateTime(2020, 1, 1, 0, 0, 0, 599000, precision=3)
		>>> msg_alarm(ti)
		b'ALARM 2020-01-01T00:00:00.599Z'

	:param obspy.core.utcdatetime.UTCDateTime event_time: the datetime object to serialize and convert to bytes
	:rtype: bytes
	:return: the ``ALARM`` message, ready to be put on the queue
	'''
	return b'ALARM %s' % bytes(str(event_time), 'utf-8')


def msg_reset(reset_time):
	'''
	This function constructs the ``RESET`` message as a bytes object.
	Currently this is only used by :py:class:`rsudp.p_producer.Producer`
	to construct reset queue messages.

	For example:

	.. code-block:: python

		>>> from obspy import UTCDateTime
		>>> ti = UTCDateTime(2020, 1, 1, 0, 0, 0, 599000, precision=3)
		>>> msg_reset(ti)
		b'RESET 2020-01-01T00:00:00.599Z'

	:param obspy.core.utcdatetime.UTCDateTime reset_time: the datetime object to serialize and convert to bytes
	:rtype: bytes
	:return: the ``RESET`` message, ready to be put on the queue
	'''
	return b'RESET %s' % bytes(str(reset_time), 'utf-8')


def msg_imgpath(event_time, figname):
	'''
	This function constructs the ``IMGPATH`` message as a bytes object.
	Currently this is only used by :py:class:`rsudp.c_plot.Plot`
	to construct queue messages containing timestamp and saved image path.

	For example:

	.. code-block:: python

		>>> from obspy import UTCDateTime
		>>> ti = UTCDateTime(2020, 1, 1, 0, 0, 0, 599000, precision=3)
		>>> path = '/home/pi/rsudp/screenshots/test.png'
		>>> msg_imgpath(ti, path)
		b'IMGPATH 2020-01-01T00:00:00.599Z /home/pi/rsudp/screenshots/test.png'

	:param obspy.core.utcdatetime.UTCDateTime event_time: the datetime object to serialize and convert to bytes
	:param str figname: the figure path as a string
	:rtype: bytes
	:return: the ``IMGPATH`` message, ready to be put on the queue
	'''
	return b'IMGPATH %s %s' % (bytes(str(event_time), 'utf-8'), bytes(str(figname), 'utf-8'))


def msg_term():
	'''
	This function constructs the simple ``TERM`` message as a bytes object.

	.. code-block:: python

		>>> msg_term()
		b'TERM'


	:rtype: bytes
	:return: the ``TERM`` message
	'''
	return b'TERM'


def get_msg_time(msg):
	'''
	This function gets the time from ``ALARM``, ``RESET``,
	and ``IMGPATH`` messages as a UTCDateTime object.

	For example:

	.. code-block:: python

		>>> from obspy import UTCDateTime
		>>> ti = UTCDateTime(2020, 1, 1, 0, 0, 0, 599000, precision=3)
		>>> path = '/home/pi/rsudp/screenshots/test.png'
		>>> msg = msg_imgpath(ti, path)
		>>> msg
		b'IMGPATH 2020-01-01T00:00:00.599Z /home/pi/rsudp/screenshots/test.png'
		>>> get_msg_time(msg)
		UTCDateTime(2020, 1, 1, 0, 0, 0, 599000)

	:param bytes msg: the bytes-formatted queue message to decode
	:rtype: obspy.core.utcdatetime.UTCDateTime
	:return: the time embedded in the message
	'''
	return rs.UTCDateTime.strptime(msg.decode('utf-8').split(' ')[1], '%Y-%m-%dT%H:%M:%S.%fZ')


def get_msg_path(msg):
	'''
	This function gets the path from ``IMGPATH`` messages as a string.

	For example:

	.. code-block:: python

		>>> from obspy import UTCDateTime
		>>> ti = UTCDateTime(2020, 1, 1, 0, 0, 0, 599000, precision=3)
		>>> path = '/home/pi/rsudp/screenshots/test.png'
		>>> msg = msg_imgpath(ti, path)
		>>> msg
		b'IMGPATH 2020-01-01T00:00:00.599Z /home/pi/rsudp/screenshots/test.png'
		>>> get_msg_path(msg)
		'/home/pi/rsudp/screenshots/test.png'

	:param bytes msg: the bytes-formatted queue message to decode
	:rtype: str
	:return: the path embedded in the message
	'''
	return msg.decode('utf-8').split(' ')[2]


def deconv_vel_inst(self, trace, output):
	'''
	.. role:: pycode(code)
		:language: python

	A helper function for :py:func:`rsudp.raspberryshake.deconvolve`
	for velocity channels.

	:param self self: The self object of the sub-consumer class calling this function.
	:param obspy.core.trace.Trace trace: the trace object instance to deconvolve
	'''
	if self.deconv not in 'CHAN':
		trace.remove_response(inventory=rs.inv, pre_filt=[0.1, 0.6, 0.95*self.sps, self.sps],
								output=output, water_level=4.5, taper=False)
	else:
		trace.remove_response(inventory=rs.inv, pre_filt=[0.1, 0.6, 0.95*self.sps, self.sps],
								output='VEL', water_level=4.5, taper=False)
	if 'ACC' in self.deconv:
		trace.data = rs.np.gradient(trace.data, 1)
	elif 'GRAV' in self.deconv:
		trace.data = rs.np.gradient(trace.data, 1) / rs.g
		trace.stats.units = 'Earth gravity'
	elif 'DISP' in self.deconv:
		trace.data = rs.np.cumsum(trace.data)
		trace.taper(max_percentage=0.1, side='left', max_length=1)
		trace.detrend(type='demean')
	else:
		trace.stats.units = 'Velocity'

def deconv_acc_inst(self, trace, output):
	'''
	.. role:: pycode(code)
		:language: python

	A helper function for :py:func:`rsudp.raspberryshake.deconvolve`
	for acceleration channels.

	:param self self: The self object of the sub-consumer class calling this function.
	:param obspy.core.trace.Trace trace: the trace object instance to deconvolve
	'''

	if len(trace.data) >= 1000:
			lowcut = get_low_corner_freq(trace, noise_type="lowest_ave")

			if lowcut <= 0.1:
					lowcut = 0.1
			elif lowcut <= 0.5:
					lowcut = 0.3
			else:
					lowcut = 0.5

	if self.deconv not in 'CHAN':
		trace.remove_response(inventory=rs.inv, output=output, taper=True, taper_fraction=0.1,
																			pre_filt=False, water_level=4.5)
	else:
		trace.remove_response(inventory=rs.inv, output='ACC', taper=True, taper_fraction=0.1,
															pre_filt=False, water_level=4.5)

	if len(trace.data) >= 1000:
			trace.data = bandpass(trace.data, lowcut, 0.49*self.sps, df=self.sps, corners=4, zerophase=True)

	if 'VEL' in self.deconv:
		trace.data = rs.np.cumsum(trace.data)
		trace.detrend(type='demean')

	elif 'DISP' in self.deconv:
		try:
			updated_trace = differentiate(improved_integration(trace))
			trace.data = updated_trace.data
		except Exception as e:
			print(COLOR['red'] + '[helpers.py][deconv_acc_inst] Failed to differentiate on "improved integration" for deconv="DISP", using original code...' + COLOR['white'], e)
			trace.data = rs.np.cumsum(rs.np.cumsum(trace.data))
			trace.detrend(type='linear')

	elif 'GRAV' in self.deconv:
		trace.data = trace.data / rs.g
		trace.stats.units = 'Earth gravity'
	else:
		trace.stats.units = 'Acceleration'
	if ('ACC' not in self.deconv) and ('CHAN' not in self.deconv):
		trace.taper(max_percentage=0.1, side='left', max_length=1)


def deconv_rbm_inst(self, trace, output):
	'''
	.. role:: pycode(code)
		:language: python

	A helper function for :py:func:`rsudp.raspberryshake.deconvolve`
	for Raspberry Boom pressure transducer channels.

	.. note::

		The Raspberry Boom pressure transducer does not currently have a
		deconvolution function. The Raspberry Shake team is working on a
		calibration for the Boom, but until then Boom units are given in
		counts.

	:param self self: The self object of the sub-consumer class calling this function.
	:param obspy.core.trace.Trace trace: the trace object instance to deconvolve
	'''
	trace.stats.units = ' counts'


def deconvolve(self):
	'''
	.. role:: pycode(code)
		:language: python

	A central helper function for sub-consumers (i.e. :py:class:`rsudp.c_plot.Plot` or :py:class:`rsudp.c_alert.Alert`)
	that need to deconvolve their raw data to metric units.
	Consumers with :py:class:`obspy.core.stream.Stream` objects in :pycode:`self.stream` can use this to deconvolve data
	if this library's :pycode:`rsudp.raspberryshake.inv` variable
	contains a valid :py:class:`obspy.core.inventory.inventory.Inventory` object.

	:param self self: The self object of the sub-consumer class calling this function. Must contain :pycode:`self.stream` as a :py:class:`obspy.core.stream.Stream` object.
	'''
	acc_channels = ['ENE', 'ENN', 'ENZ']
	vel_channels = ['EHE', 'EHN', 'EHZ', 'SHZ']
	rbm_channels = ['HDF']

	self.stream = self.raw.copy()
	for trace in self.stream:
		trace.stats.units = self.units
		output = 'ACC' if self.deconv == 'GRAV' else self.deconv	# if conversion is to gravity
		if self.deconv:
			if trace.stats.channel in vel_channels:
				deconv_vel_inst(self, trace, output)	# geophone channels

			elif trace.stats.channel in acc_channels:
				deconv_acc_inst(self, trace, output)	# accelerometer channels

			elif trace.stats.channel in rbm_channels:
				deconv_rbm_inst(self, trace, output)	# this is the Boom channel

			else:
				trace.stats.units = ' counts'	# this is a new one

		else:
			trace.stats.units = ' counts'		# this is not being deconvolved


def resolve_extra_text(extra_text, max_len, sender='helpers'):
	'''
	.. role:: pycode(code)
		:language: python

	.. versionadded:: 1.0.3

	A central helper function for the :class:`rsudp.c_telegram.Tweeter`
	and :class:`rsudp.c_telegram.Telegrammer` classes that checks whether
	the :pycode:`"extra_text"` parameter (in the settings file) is of appropriate
	length. This is done to avoid errors when posting alerts.
	The function will truncate longer messages.

	:param str extra_text: String of additional characters to post as part of the alert message (longer messages will be truncated).
	:param str max_len: Upper limit of characters accepted in message (280 for Twitter, 4096 for Telegram).
	:param str sender: String identifying the origin of the use of this function (:pycode:`self.sender` in the source function).
	:rtype: str
	:return: the message string to be incorporated

	'''
	allowable_len = max_len - 177	# length of string allowable given maximum message text & region
	if ((extra_text == '') or (extra_text == None) or (extra_text == False)):
		return ''
	else:
		extra_text = str(extra_text)
		len_ex_txt = len(extra_text)

		if len_ex_txt > allowable_len:
			printW('extra_text parameter is longer than allowable (%s chars) and will be truncated. Please keep extra_text at or below %s characters.' % (len_ex_txt, allowable_len), sender=sender)
			extra_text = extra_text[:allowable_len]

		return ' %s' % (extra_text)

############################
### additional functions ###
############################

def msg_process(max_values):
		'''
		This function constructs the ``PROCESS`` message as a bytes object.
		Currently this is only used by :py:class:`rsudp.p_producer.Producer`
		to construct process queue messages.
		For example:
		.. code-block:: python
				>>> max_pga = 0.8800480717294786 # m/s^2 (meters per second squared)
				>>> max_pgd = 6.899747467484326e-06 # m (meters)
				>>> max_pga_channel = "ENE"
				>>> max_pgd_channel = "ENN"
				>>> event_time = "2023-04-26T04:26:12.02Z"
				>>> msg_process(max_values)
				b'PROCESS {"max_pga":0.44449061403448303,"max_pgd":6.130023442598087e-06,"max_pga_channel":"ENN","max_pgd_channel":"ENN","event_time":"2023-04-26T04:26:12.02Z"}'
		:param tuple event_time: a tuple with the maximum peak ground acceleration and
				maximum peak ground displacement as the first and second entries, respectively
		:rtype: bytes
		:return: the ``PROCESS`` message, ready to be put on the queue
		'''

		# remove spaces -- this is critical in `get_msg_process_values` so do not remove
		max_values = max_values.replace(' ', '')
		return b'PROCESS %s' % (bytes(str(max_values), 'utf-8'))

def get_msg_process_values(msg):
		'''
		This function gets the max values from ``PROCESS`` messages as a string.
		For example:
		.. code-block:: python
				>>> msg = b'PROCESS {"max_pga":0.26285487778758243,"max_pgd":2.3574178136785185e-06,"max_pga_channel":"ENN","max_pgd_channel":"ENN","event_time":"2023-04-26T04:48:52.27Z"}'
				>>> get_msg_process_values(msg)
				{'max_pga': 0.26285487778758243, 'max_pgd': 2.3574178136785185e-06, 'max_pga_channel': 'ENN', 'max_pgd_channel': 'ENN', 'event_time': '2023-04-26T04:48:52.27Z'}
		:param bytes msg: the bytes-formatted queue message to decode
		:rtype: tuple
		:return: the max values part of the ``PROCESS`` message as a tuple
		'''
		decoded_msg_arr = msg.decode('utf-8').split(' ')
		max_values_str = decoded_msg_arr[1]
		max_values_dict = json.loads(max_values_str)
		return max_values_dict

def g_to_intensity(g):
		'''
		Gets intensity from PGA.
		Author unknown. Inspect changes in https://github.com/jadurani/rsudp/pull/1/files
		Inherited by @jadurani.
		'''
		intensity_scale = {
			(0,0.00170): 'I',
			(0.00170,0.01400): 'II-III',
			(0.01400,0.03900): 'IV',
			(0.03900,0.09200): 'V',
			(0.09200,0.18000): 'VI',
			(0.18000,0.34000): 'VII',
			(0.34000,0.65000): 'VIII',
			(0.65000,1.24000): 'IX',
			(1.24000,5): 'X+'
		}
		intensity = 'X+'
		for i in intensity_scale:
			if i[0] < g < i[1]:
					intensity = intensity_scale[i]
		return intensity

def intensity_to_int(intensity):
		'''
		Convert string to number for text-to-voice
		Author unknown. Inspect changes in https://github.com/jadurani/rsudp/pull/1/files
		Inherited by @jadurani.
		'''
		if intensity == "I":
				intensityNum = 1
		elif intensity == "II-III":
				intensityNum = 2
		elif intensity == "IV":
				intensityNum = 4
		elif intensity == "V":
				intensityNum = 5
		elif intensity == "VI":
				intensityNum = 6
		elif intensity == "VII":
				intensityNum = 7
		elif intensity == "VIII":
				intensityNum = 8
		elif intensity == "IX":
				intensityNum = 9
		elif intensity == "X+":
				intensityNum = 10
		else:
				intensityNum = 0

		return intensityNum

def get_intensity_alert_text(pga):
	max_intensity_str = g_to_intensity(pga/9.81)
	max_intensity_int = intensity_to_int(max_intensity_str)

	if max_intensity_str == "II-III":
		return "Earthquake detected at intensity two or three"

	return "Earthquake detected at intensity %.0f" % max_intensity_int

def get_pga_pgd_alert_text(pga, pgd):
	return ("Peak displacement is %.2f meters and peak acceleration is %.2f meters per second squared ") % (pgd, pga)


def get_low_corner_freq(tr, low_power_thresh = 0.0001, noise_type="use_end", plot=False, save_plot=False, plot_info=None, verbose=False):
		'''
		Written by unknown author.
		Inherited by @jadurani. Note: I haven't fully delved into studying what this function does. I only updated the part regarding the
		masked values which I've only experienced to appear when I've set the "station" value to one that is not within my local area network.
		'''
		tr = tr.copy()

		window_size = int(0.10*len(tr.data)) # get 10% length of data
		# window_size = len(tr.data)

		# Check if the Trace has masked values. (Writted by @jadurani, not sure on the resulting computation)
		# When receiving data from a raspberry shake machine not within LAN, masked values may appear
		if np.ma.is_masked(tr.data):
				print(COLOR['red'] + "[helpers.py][get_low_corner_freq] The Trace contains masked values. Unmasking..." + COLOR['white'])
				tr.data = np.ma.filled(tr.data)
				print(COLOR['yellow'] + "[helpers.py][get_low_corner_freq] Done. However, do note that this may have side-effects on the computed values." + COLOR['white'])

		if noise_type == "use_end":
				# print(tr.data.dtype)
				noise = tr.data[-1*int(window_size-1*tr.stats.sampling_rate):] # remove one second worth of samples
				# print(int(window_size-1*tr.stats.sampling_rate))
		elif noise_type == "lowest_ave":
				tr = tr.copy()
				tr.detrend("linear") # remove dc
				windowed_ave_arr = rs.np.convolve(rs.np.absolute(tr.data[window_size:]), rs.np.ones(window_size), 'valid')/window_size
														# convolve takes inner product of the two arrays and sum them,
														# take abs to avoid cancelling of positive and negative amps
														# skip first window size to avoid it being the minimum
														# valid is to only perform when overlap is complete
				last_occur_min_index = rs.np.argmin(windowed_ave_arr[::-1])
				last_occur_min_index = len(windowed_ave_arr) - last_occur_min_index - 1
														# get first occur of min in reversed arr to get last occur
														# then flip to normal indices
				noise_end_ind = 2*window_size + last_occur_min_index
				noise_start_ind = noise_end_ind - window_size
				noise = tr.data[noise_start_ind : noise_end_ind + 1]
		else: # get noise from beginning
				noise = tr.data[:int(window_size-1*tr.stats.sampling_rate)] # remove one second worth of samples

		# get responses
		signal = tr.detrend("linear").data
		signal_resp = abs(rs.np.fft.rfft(signal, n=_npts2nfft(len(signal)))) # get distance as magnitude
		# signal_resp_x = rs.np.fft.rfftfreq(_npts2nfft(len(signal)), 1/tr.stats.sampling_rate)
		noise = noise - rs.np.mean(noise) #remove DC
		noise_resp = abs(rs.np.fft.rfft(noise, n=_npts2nfft(len(noise)))) # get distance as magnitude
		noise_resp = resample(noise_resp, len(signal_resp))
		#noise_resp_x = rs.np.fft.rfftfreq(_npts2nfft(len(noise)), 1/tr.stats.sampling_rate)
		noise_resp_x = rs.np.fft.rfftfreq(_npts2nfft(len(signal)), 1/tr.stats.sampling_rate)
		nyquist_ind = len(noise_resp)//2

		noise_integral = integrate.cumtrapz(signal_resp[:nyquist_ind]-noise_resp[:nyquist_ind], noise_resp_x[:nyquist_ind], initial=0) # only up to nyquist freq
		noise_integral = noise_integral/noise_integral[-1] # normalize w max
		# linearly approximate lowcut
		# lowcut_ind = int((noise_integral > low_power_thresh).nonzero()[0][0])
		lowcut = rs.np.interp(low_power_thresh, noise_integral, noise_resp_x[:nyquist_ind]) # inverted

		return lowcut


def improved_integration(tr):
		'''
		Unknown author. Possibly @jermz
		'''
		tr = tr.copy()
		tr.detrend("demean") # make sure no constant that will become linear function
		tr.integrate(method="cumtrapz")
		tr.detrend("linear") # (mx+b, ie the leakage due to cumtrapz)
		return tr

def differentiate(tr):
		'''
		Unknown author. Possibly @jermz
		'''
		tr = tr.copy()
		tr.differentiate(method="gradient")

		return tr