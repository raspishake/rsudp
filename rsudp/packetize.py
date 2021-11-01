#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
import getopt
from obspy import read
from datetime import timedelta
from rsudp.test import TEST
from rsudp.helpers import lesser_multiple


SMP = {
	0.01: 25,
	0.02: 50,
}


def get_samps(stream):
	'''
	Return the number of samples to place in each packet.
	This number is based on the sampling frequency of the data in question.

	Raspberry Shake data is sent to the UDP port either in packets of 25
	(for sampling frequency of 100 Hz) or 50 (for frequency of 50 Hz).

	This is hardcoded and will not change for the foreseeable future,
	which means that it can be used to determine the variety of sensor used
	(50 Hz is the original versions of RS1D).

	:param obspy.core.stream.Stream stream: Stream object to calculate samples per packet for

	:rtype: int
	:return: the number of samples per packet (either 25 or 50)
	'''
	try:
		return SMP[stream[0].stats.delta]
	except KeyError as e:
		raise KeyError('Sampling frequency of %s is not supported. Is this Raspberry Shake data?' % (e))


def cutoff_calc(stream):
	'''
	Return the number of samples that will be transcribed to UDP packet formatted ascii text.
	Iterates over each trace in the stream to make this calculation.

	:param obspy.core.stream.Stream stream: Stream object to calculate number of samples from

	:rtype: int, int
	:return: 1) the number of samples to transcribe, 2) the number of samples in each packet
	'''
	samps = get_samps(stream)
	c = lesser_multiple(len(stream[0].data), base=samps)
	for t in stream:
		n = lesser_multiple(len(t.data), base=samps)
		if n < c:
			c = n
	return c, samps


def packetize(inf, outf, testing=False):
	'''
	Reads a seismic data file and converts it to ascii text.

	:param str inf: the input data file to convert
	:param str outf: where to write the output file
	'''
	if os.path.isfile(os.path.expanduser(inf)):
		stream = read(inf)
		cutoff, samps = cutoff_calc(stream)
		n = 0
		time = stream[0].stats.starttime

		with open(outf, 'w') as f:
			for i in range(0, int(cutoff/samps)):
				ptime = time + timedelta(seconds=stream[0].stats.delta*n)
				for t in stream:
					data = ''
					chan = t.stats.channel
					for j in range(n, n+samps):
						data += ', %s' % t.data[j]
					line = "{'%s', %.3f%s}%s" % (chan, ptime.timestamp, data, os.linesep)
					f.write(line)
				n += samps

			f.write('TERM%s' % (os.linesep))

		print('Data written to %s' % outf)
		if testing:
			TEST['x_packetize'][1] = True
	else:
		print('Input file does not exist: %s' % inf)


def main():
	'''
	This function reads command line arguments, then calls
	:py:func:`rsudp.packetize.packetize` with those arguments.
	'''
	inf, outf = False, False
	opts = getopt.getopt(sys.argv[1:], 'i:o:',
			['in=', 'out=',]
			)[0]

	for opt, arg in opts:
		if opt in ('-i', '--in='):
			inf = arg
		if opt in ('-o', '--out='):
			outf = arg
	if inf and outf:
		packetize(inf=inf, outf=outf)
	else:
		print('Usage: packetize.py -i infile.ms -o testdata')

if __name__ == '__main__':
	main()