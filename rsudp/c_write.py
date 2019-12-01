import sys, os
from threading import Thread
import time
from datetime import datetime, timedelta
from obspy import UTCDateTime
import rsudp.raspberryshake as RS
from rsudp import printM
import rsudp

class Write(Thread):
	"""
	A simple routine to write daily miniSEED data to `output_dir/data`.
	"""
	def __init__(self, q=False, debug=False, cha='all'):
		"""
		Initialize the process
		"""
		super().__init__()
		self.sender = 'Write'
		self.alive = True

		if q:
			self.queue = q
		else:
			printM('ERROR: no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			sys.exit()

		self.stream = RS.Stream()
		self.outdir = rsudp.data_dir
		self.debug = debug
		self.chans = []
		cha = RS.chns if (cha == 'all') else cha
		cha = list(cha) if isinstance(cha, str) else cha
		l = RS.chns
		for c in l:
			n = 0
			for uch in cha:
				if (uch.upper() in c) and (c not in str(self.chans)):
					self.chans.append(c)
				n += 1
		if len(self.chans) < 1:
			self.chans = RS.chns
		printM('Writing channels: %s' % self.chans, self.sender)
		self.numchns = RS.numchns
		self.stime = 1/RS.sps
		self.inv = RS.inv
		self.alarm = False
		printM('Starting.', self.sender)

	def getq(self):
		d = self.queue.get(True, timeout=None)
		self.queue.task_done()
		if 'TERM' in str(d):
			self.alive = False
			printM('Exiting.', self.sender)
			sys.exit()
		elif 'ALARM' in str(d):
			pass
		else:
			if RS.getCHN(d) in self.chans:
				self.stream = RS.update_stream(
					stream=self.stream, d=d, fill_value=None)
				return True
			else:
				return False
	
	def set_sps(self):
		self.sps = self.stream[0].stats.sampling_rate

	def elapse(self, new=False):
		self.st = UTCDateTime.now()
		self.y, self.m, self.d = self.st.year, self.st.month, self.st.day
		self.j = self.st.strftime('%j')
		self.newday = UTCDateTime(self.y, self.m, self.d, 0, 0) + timedelta(days=1.1)
		self.newday = UTCDateTime(self.newday.year, self.newday.month, self.newday.day, 0, 0)
		if new:
			self.last = self.newday
		else:
			self.last = self.st

	def slicestream(self):
		self.stream.slice(starttime=self.last)

	def write(self, stream=False):
		if not stream:
			self.last = self.stream[0].stats.endtime - timedelta(seconds=5)
			stream = self.stream.copy().slice(
						endtime=self.last, nearest_sample=False)

		for t in stream:
			enc = 'STEIM2'	# encoding
			if isinstance(t.data, RS.np.ma.masked_array):
				t.data = t.data.filled(fill_value=0) # fill array (to avoid obspy write error)
			outfile = self.outdir + '/%s.%s.00.%s.D.%s.%s' % (t.stats.network,
								t.stats.station, t.stats.channel, self.y, self.j)
			if os.path.exists(os.path.abspath(outfile)):
				with open(outfile, 'ab') as fh:
					if self.debug:
						printM('Writing %s records to %s'
								% (len(t.data), outfile), self.sender)
					t.write(fh, format='MSEED', encoding=enc)
			else:
				if self.debug:
					printM('Writing %s new file %s'
							% (len(t.data), outfile), self.sender)
				t.write(outfile, format='MSEED', encoding=enc)

	def run(self):
		"""
		"""
		self.elapse()

		self.getq()
		self.set_sps()
		self.getq()
		printM('miniSEED output directory: %s' % (self.outdir), self.sender)
		if self.inv:
			printM('Writing inventory file: %s/%s.%s.00.xml' % (self.outdir,
					self.stream[0].stats.network,
					self.stream[0].stats.station), self.sender)
			self.inv.write('%s/%s.%s.00.xml' % (self.outdir,
					self.stream[0].stats.network,
					self.stream[0].stats.station),
					format='STATIONXML')
		printM('Beginning miniSEED output.', self.sender)
		wait_pkts = (self.numchns * 10) / (RS.tf / 1000) 		# comes out to 10 seconds (tf is in ms)

		n = 0
		while True:
			while True:
				if self.queue.qsize() > 0:
					self.getq()
					time.sleep(0.01)		# wait a few ms to see if another packet will arrive
					n += 1
				else:
					self.getq()
					n += 1
					break
			if n >= wait_pkts:
				if self.newday < UTCDateTime.now(): # end of previous day and start of new day
					self.write(self.stream.slice(
								endtime=self.newday, nearest_sample=False))
					self.stream = self.stream.slice(
								starttime=self.newday, nearest_sample=False)
					self.elapse(new=True)
				else:
					self.write()
					self.stream = self.stream.slice(
								starttime=self.last, nearest_sample=False)
				self.stream = RS.copy(self.stream)
				n = 0

				self.getq()
				time.sleep(0.01)		# wait a few ms to see if another packet will arrive
			sys.stdout.flush()
			sys.stderr.flush()
