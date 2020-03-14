import os, sys
import getopt
from obspy import read
from datetime import timedelta

SMP = {
	0.01: 25,
	0.02: 50,
}

def packetize(inf, outf):
	'''
	Reads a seismic data file and converts it to ascii text.

	:param str inf: the input data file to convert
	:param str outf: where to write the output file
	'''
	if os.path.isfile(os.path.expanduser(inf)):
		stream = read(inf)
		samps = SMP[stream[0].stats.delta]
		n = 0
		time = stream[0].stats.starttime

		with open(outf, 'w') as f:
			for i in range(0, int(len(stream[0].data)/samps)):
				ptime = time + timedelta(seconds=stream[0].stats.delta*n)
				for t in stream:
					data = ''
					chan = t.stats.channel
					for i in range(n, n+samps):
						data += ', %s' % t.data[i]
					line = "{'%s', %.3f%s}%s" % (chan, ptime.timestamp, data, os.linesep)
					f.write(line)
				n += samps

			f.write('TERM%s' % (os.linesep))

		print('Data written to %s' % outf)
	else:
		print('Input file does not exist.')


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