from obspy.core.trace import Trace
from obspy.core.stream import Stream
from obspy.core.utcdatetime import UTCDateTime
from datetime import datetime, timedelta
import numpy as np
import raspberryShake as RS


# The call letters of the station
sta = 'RCB43'		# this example is a RS1D in Williamstown, MA, USA
port = 18005		# port on the local machine that the RS is sending data to

'''
This program demonstrates the ease with which you can turn Raspberry Pi UDP data into a fully functional obspy stream.

We do that by taking the following steps.

1. open socket at port listed above
2. create empty obspy stream
3. get a data packet and analyze inherent values
4. create trace(s) and assign inherent values and data
5. append trace to obspy stream
6. repeat 3 - 5

So in a program that uses this library, you'd want to first call init_stream() to create a stream object,
then loop over update_stream(stream) to continously append traces to that stream object.
Your stream object should contain traces representing all channels sent to the port above.
Traces should be appended and merged per channel automatically.
'''

channels = {}

def make_trace():								# makes a trace and assigns it some values using a data packet
	d = RS.getDATA()							# get a data packet
	ch = RS.getCHN(d)							# channel
	t = RS.getTIME(d)							# unix epoch time since 1970-01-01 00:00:00Z, or as obspy calls it, "timestamp"
	sps = RS.getSR(RS.getTR(RS.getCHN(d)))		# samples per second
	st = RS.getSTREAM(d)						# samples in data packet in list [] format
	tr = Trace()								# create empty trace
	tr.stats.network = 'AM'						# assign values
	tr.stats.location = '00'
	tr.stats.station = sta
	tr.stats.channel = ch
	tr.stats.sampling_rate = sps
	tr.stats.starttime = UTCDateTime(t)
	tr.data = np.ma.MaskedArray(st)
	return tr

def init_stream():								# opens port and creates first trace object
	RS.openSOCK(port)
	stream = Stream()
	i = 0
	for chn in RS.getCHNS():
		trace = make_trace()
		stream.append(trace)
		channels[trace.stats.channel] = i
		i += 1
	return stream

def update_stream(stream):
	trace = make_trace()
	return stream[channels[trace.stats.channel]].__add__(trace, method=1, interpolation_samples=0,
														 fill_value=None, sanity_checks=False)
