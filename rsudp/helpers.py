import rsudp.raspberryshake as rs
from rsudp import COLOR, printM, printW
import os
import json


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
    "duration": 90,
    "spectrogram": true,
    "fullscreen": false,
    "kiosk": false,
    "eq_screenshots": false,
    "channels": ["all"],
    "deconvolve": true,
    "units": "CHAN"},
"forward": {
    "enabled": false,
    "address": ["192.168.1.254"],
    "port": [8888],
    "channels": ["all"],
    "fwd_data": true,
    "fwd_alarms": false},
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
    "units": "VEL"},
"alertsound": {
    "enabled": false,
    "mp3file": "doorbell"},
"custom": {
    "enabled": false,
    "codefile": "n/a",
    "win_override": false},
"tweets": {
    "enabled": false,
    "tweet_images": true,
    "api_key": "n/a",
    "api_secret": "n/a",
    "access_token": "n/a",
    "access_secret": "n/a",
    "extra_text": ""},
"telegram": {
    "enabled": false,
    "send_images": true,
    "token": "n/a",
    "chat_id": "n/a",
    "extra_text": ""},
"rsam": {
    "enabled": false,
    "quiet": true,
    "fwaddr": "192.168.1.254",
    "fwport": 8887,
    "fwformat": "LITE",
    "channel": "HZ",
    "interval": 10,
    "deconvolve": false,
    "units": "VEL"}
}

""" % (output_dir)
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
			print(COLOR['red'] + '       detail: %s' % e + COLOR['white'])
			print(COLOR['red'] + '       If you would like to overwrite and rebuild the file, you can enter the command below:' + COLOR['white'])
			print(COLOR['bold'] + '       shake_client -d %s' % loc + COLOR['white'])
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
		2020-03-25 01:35:04 [conn_stats]                 Port: 18069
		2020-03-25 01:35:04 [conn_stats]   Sending IP address: 192.168.0.4
		2020-03-25 01:35:04 [conn_stats]     Set station name: R24FA
		2020-03-25 01:35:04 [conn_stats]   Number of channels: 4
		2020-03-25 01:35:04 [conn_stats]   Transmission freq.: 250 ms/packet
		2020-03-25 01:35:04 [conn_stats]    Transmission rate: 4 packets/sec
		2020-03-25 01:35:04 [conn_stats]   Samples per second: 100 sps
		2020-03-25 01:35:04 [conn_stats]            Inventory: AM.R24FA (Raspberry Shake Citizen Science Station)

	:param bool TESTING: if ``True``, text is printed to the console in yellow. if not, in white.
	'''
	s = 'conn_stats'
	pf = printW if TESTING else printM
	pf('Initialization stats:', sender=s, announce=False)
	pf('                Port: %s' % rs.port, sender=s, announce=False)
	pf('  Sending IP address: %s' % rs.firstaddr, sender=s, announce=False)
	pf('    Set station name: %s' % rs.stn, sender=s, announce=False)
	pf('  Number of channels: %s' % rs.numchns, sender=s, announce=False)
	pf('  Transmission freq.: %s ms/packet' % rs.tf, sender=s, announce=False)
	pf('   Transmission rate: %s packets/sec' % rs.tr, sender=s, announce=False)
	pf('  Samples per second: %s sps' % rs.sps, sender=s, announce=False)
	if rs.inv:
		pf('           Inventory: %s' % rs.inv.get_contents()['stations'][0],
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
	if self.deconv not in 'CHAN':
		trace.remove_response(inventory=rs.inv, pre_filt=[0.1, 0.6, 0.95*self.sps, self.sps],
								output=output, water_level=4.5, taper=False)
	else:
		trace.remove_response(inventory=rs.inv, pre_filt=[0.1, 0.6, 0.95*self.sps, self.sps],
								output='ACC', water_level=4.5, taper=False)
	if 'VEL' in self.deconv:
		trace.data = rs.np.cumsum(trace.data)
		trace.detrend(type='demean')
	elif 'DISP' in self.deconv:
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
