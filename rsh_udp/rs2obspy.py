from obspy.core.trace import Trace
from obspy.core.stream import Stream
from obspy.core.utcdatetime import UTCDateTime
from obspy import read_inventory
from datetime import timedelta
import numpy as np
import rsh_udp.raspberryshake as RS


'''
This program demonstrates the ease with which you can turn Raspberry Pi UDP data into a fully functional obspy stream.

We do that by taking the following steps.

1. open socket at port using init(port=XXXX, sta='RCB43', sta='AM')
2. set samples per second value (requires two getDATA calls, so we leave it out of the normal workflow)
3. create a blank stream object
4. get a data packet and calculate inherent values
5. create trace and assign inherent values and data
6. append trace to obspy stream and merge, so that number of channels = number of traces
7. repeat 4 - 6 to continue adding data to stream

So in a program that uses this library, you'd want to first call init_stream() to create a stream object,
then loop over update_stream(stream) to continously append traces to that stream object.
Your stream object should contain traces representing all channels sent to the port above.
Traces should be appended and merged to one per channel automatically.
'''

def init(port=8888, sta='Z0000', timeout=10):
	global sps, channels, inv, trate
	RS.initRSlib(dport=port, rssta=sta, timeout=timeout)
	RS.openSOCK()
	d = RS.getDATA()
	trate = RS.getTR(RS.getCHN(d))
	sps = RS.getSR(trate, d)
	RS.printM('Got data with sampling rate %s Hz (calculated from channel %s)' % (sps, RS.getCHN(d)))
	channels = RS.getCHNS()
	channelstring = ''
	for channel in channels:
		channelstring += channel + ' '
	RS.printM('Found %s channel(s): %s' % (len(channels), channelstring))
	if 'Z0000' in sta:
		RS.printM('No station name given, continuing without inventory.')
		inv = False
	else:
		try:
			RS.printM('Fetching inventory for station %s.%s from Raspberry Shake FDSN.' % (RS.net, RS.sta))
			inv = read_inventory('https://fdsnws.raspberryshakedata.com/fdsnws/station/1/query?network=%s&station=%s&level=resp&format=xml'
								 % (RS.net, RS.sta))
			RS.printM('Inventory fetch successful.')
		except:
			RS.printM('Inventory fetch failed, continuing without.')
			inv = False

def make_trace():
	'''Makes a trace and assigns it some values using a data packet.'''
	d = RS.getDATA()							# get a data packet
	ch = RS.getCHN(d)							# channel
	t = RS.getTIME(d)							# unix epoch time since 1970-01-01 00:00:00Z, or as obspy calls it, "timestamp"
	st = RS.getSTREAM(d)						# samples in data packet in list [] format
	tr = Trace()								# create empty trace
	tr.stats.network = RS.net						# assign values
	tr.stats.location = '00'
	tr.stats.station = RS.sta
	tr.stats.channel = ch
	tr.stats.sampling_rate = sps
	tr.stats.starttime = UTCDateTime(t)
	if inv:
		try:
			tr.attach_response(inv)
		except:
			RS.printM('ERROR attaching inventory response. Are you sure you set the station name correctly?')
			RS.printM('    This could indicate a mismatch in the number of data channels between the inventory and the stream.')
			RS.printM('    For example, if you are receiving RS4D data, please make sure the inventory you download has 4 channels.')
	tr.data = np.ma.MaskedArray(st)
	return tr


## Call these methods in succession to initialize a stream, then add traces to it
# Call this once
def init_stream():
	'''Returns the initial stream object with one trace.'''
	RS.printM('Initializing Stream object.')
	stream = Stream().append(make_trace())
	if inv:
		RS.printM('Attaching inventory response.')
		stream.attach_response(inv)
	return stream								# return new stream object with trace embedded


# Then make repeated calls to this, to continue adding trace data to the stream
def update_stream(stream, **kwargs):
	'''Returns an updated trace object with new data, merged down to one trace per available channel.'''
	return stream.append(make_trace()).merge(**kwargs)
