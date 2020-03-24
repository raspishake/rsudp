import rsudp.raspberryshake as rs


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
	:param osbpy.core.trace.Trace trace: the trace object instance to deconvolve
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
	:param osbpy.core.trace.Trace trace: the trace object instance to deconvolve
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
	:param osbpy.core.trace.Trace trace: the trace object instance to deconvolve
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


