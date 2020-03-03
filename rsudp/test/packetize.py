import os, sys
import getopt
from obspy import read
from datetime import timedelta

SMP = {
	0.01: 25,
	0.02: 50,
}

def packetize(inf, outf):
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
	opts = getopt.getopt(sys.argv[1:], 'i:o:',
			['in=', 'out=',]
			)[0]

	for opt, arg in opts:
		if opt in ('-i', 'out='):
			inf = arg
		if opt in ('-o', 'out='):
			outf = arg
	
	packetize(inf=inf, outf=outf)

if __name__ == '__main__':
	main()