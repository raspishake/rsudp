import sys, os
import time
import threading
from datetime import timedelta
from obspy import UTCDateTime
import rsudp.raspberryshake as rs
from rsudp import printM, printW, printE, helpers
from rsudp.test import TEST

class Write(rs.ConsumerThread):
	def __init__(self, q, data_dir, testing=False, debug=False, cha='all'):
		super().__init__()
		self.sender = 'Write'
		self.alive = True
		self.testing = testing
		self.debug = debug or testing
		self.queue = q

		self.stream = rs.Stream()
		self.outdir = os.path.join(data_dir, 'data')
		self.outfiles = []

		self.chans = []

        # Normalize input
		input_chans = cha if isinstance(cha, list) else [cha]

		if not (len(input_chans) == 1 and input_chans[0] == 'all'):
			valid_channels = ['SHZ', 'EHZ', 'EHE', 'EHN', 'ENZ', 'ENE', 'ENN', 'HDF']
			invalid = [ch for ch in input_chans if ch not in valid_channels]
			if invalid:
				printE(f"Invalid channel(s): {invalid}.\nMust be one (or combination) of: {valid_channels}\nQuitting.", self.sender)
				sys.exit(1)

        # This will internally resolve 'all' to the full list
		helpers.set_channels(self, cha)

		printM('Writing channels: %s' % self.chans, self.sender)
		self.numchns = rs.numchns
		self.stime = 1 / rs.sps
		self.inv = rs.inv

		self.seen_channels = {}
		self.expected_channels = set(self.chans)
		self.channel_event = threading.Event()

		printM('Starting.', self.sender)

	def getq(self):
		d = self.queue.get(True, timeout=None)
		self.queue.task_done()

		if 'TERM' in str(d):
			self.alive = False
			printM('Exiting.', self.sender)
			sys.exit()
		elif str(d.decode('UTF-8')).split(' ')[0] in ['ALARM', 'RESET', 'IMGPATH']:
			return False
		else:
			channel = rs.getCHN(d)		
			if channel in self.chans:
				self.seen_channels[channel] = time.time()
				self.stream = rs.update_stream(self.stream, d, fill_value=None)
			if self.expected_channels.issubset(self.seen_channels):
				self.channel_event.set()
				return True
			else:
				return False

	def wait_for_all_channels(self, timeout=10.0):
		"""
		Wait until all expected channels have been seen, or timeout.
		Combines pre-wait priming with efficient event-driven waiting.
		"""
		printM(f"Waiting to receive all configured channels: {sorted(self.expected_channels)}", self.sender)

		# Prime queue to process any early arrivals
		start = time.time()
		while time.time() - start < timeout:
			try:
				self.getq()
			except Exception:
				break
			if self.expected_channels.issubset(self.seen_channels):
				break

		# Wait for event
		remaining = timeout - (time.time() - start)
		self.channel_event.wait(timeout=max(0.1, remaining))

		if not self.expected_channels.issubset(self.seen_channels):
			printW(f"Timeout waiting for channels. Seen: {sorted(self.seen_channels.keys())}", self.sender)
			return False

		return True

	def set_sps(self):
		if len(self.stream) > 0:
			self.sps = self.stream[0].stats.sampling_rate

	def elapse(self, new=False):
		self.st = UTCDateTime.now()
		self.y, self.m, self.d = self.st.year, self.st.month, self.st.day
		self.j = self.st.strftime('%j')
		self.newday = UTCDateTime(self.y, self.m, self.d, 0, 0) + timedelta(days=1.1)
		self.newday = UTCDateTime(self.newday.year, self.newday.month, self.newday.day, 0, 0)
		self.last = self.newday if new else self.st

	def slicestream(self):
		self.stream.slice(starttime=self.last)

	def _tracewrite(self, t):
		enc = 'STEIM2'
		if isinstance(t.data, rs.np.ma.masked_array):
			t.data = t.data.filled(fill_value=0)
		outfile = f'{self.outdir}/{t.stats.network}.{t.stats.station}.00.{t.stats.channel}.D.{self.y}.{self.j}'
		if outfile not in self.outfiles:
			self.outfiles.append(outfile)
		if os.path.exists(outfile):
			with open(outfile, 'ab') as fh:
				t.write(fh, format='MSEED', encoding=enc)
				if self.debug:
					printM(f'{len(t.data)} records to {outfile}', self.sender)
		else:
			t.write(outfile, format='MSEED', encoding=enc)
			if self.debug:
				printM(f'{len(t.data)} records to new file {outfile}', self.sender)

	def write(self, stream=False):
		if not stream:
			self.last = self.stream[0].stats.endtime - timedelta(seconds=5)
			stream = self.stream.copy().slice(endtime=self.last, nearest_sample=False)
		for t in stream:
			self._tracewrite(t)
		if self.testing:
			TEST['c_write'][1] = True

	def run(self):
		self.elapse()
		self.wait_for_all_channels(timeout=10)

		if len(self.stream) == 0:
			printE("Stream is still empty after waiting for all channels!", self.sender)
			return

		self.set_sps()
		printM(f'miniSEED output directory: {self.outdir}', self.sender)

		if self.inv:
			stationxml = f'{self.outdir}/{self.stream[0].stats.network}.{self.stream[0].stats.station}.00.xml'
			printM(f'Writing inventory file: {stationxml}', self.sender)
			self.inv.write(stationxml, format='STATIONXML')

		printM(f'Beginning miniSEED output.\nConfigured: {self.chans} - Now writing: {sorted(self.seen_channels.keys())}', self.sender)

		wait_pkts = (self.numchns * 10) / (rs.tf / 1000)
		n = 0

		while True:
			while True:
				if self.queue.qsize() > 0:
					self.getq()
					time.sleep(0.01)
					n += 1
				else:
					self.getq()
					n += 1
					break

			if n >= wait_pkts:
				now = UTCDateTime.now()
				if self.newday < now:
					self.write(self.stream.slice(endtime=self.newday, nearest_sample=False))
					self.stream = self.stream.slice(starttime=self.newday, nearest_sample=False)
					self.elapse(new=True)
				else:
					self.write()
					self.stream = self.stream.slice(starttime=self.last, nearest_sample=False)

				self.stream = rs.copy(self.stream)
				n = 0

				self.getq()
				time.sleep(0.01)
			sys.stdout.flush()
			sys.stderr.flush()