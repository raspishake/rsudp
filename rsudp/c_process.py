import sys, os
import json

from datetime import timedelta
import rsudp.raspberryshake as rs
from obspy.signal.trigger import recursive_sta_lta
from rsudp import COLOR, printM, printW, printE, helpers
from rsudp.test import TEST

G_ACC = 9.81
class Processor(rs.ConsumerThread):
	'''
	Author unknown. Inspect changes in https://github.com/jadurani/rsudp/pull/1/files

	Inherited by @jadurani. Done cleanups of unused code. Based on the current code,
	this module reacts to the event `ALERT` and recomputes the data pushed by the
	raspishake unit across all channels. It throws "PROCESS" event after computing
	the maximum ground acceleration and maximum ground displacement. The unit is in meters.
	'''

	def __init__(self, q, data_dir, testing=False, cha='all', lta=30, deconv=False):
		'''
			Initialize the process module
			'''
		super().__init__()
		self.sender = 'Processor'
		self.alive = True
		self.testing = testing
		self.deconv = deconv

		if self.testing:
			self.debug = True

		self.fmt = '%Y-%m-%d %H:%M:%S.%f'

		self.queue = q
		self.master_queue = None

		self.chans = []
		helpers.set_channels(self, cha)

		self.stream = rs.Stream()
		self.raw = rs.Stream()
		self.outdir = os.path.join(data_dir, 'data')
		self.outfiles = []
		self.lta = lta
		self.sps = rs.sps
		self.inv = rs.inv

		self.maxstalta = 0
		self.units = 'counts'

		self.chans = []
		helpers.set_channels(self, cha)

		printM('Starting.', self.sender)

	def getq(self):
		'''
		Reads data from the queue and updates the stream.

		:rtype: bool
		:return: Returns ``True`` if stream is updated, otherwise ``False``.
			'''

		d = self.queue.get()
		self.queue.task_done()

		if 'TERM' in str(d):
			self.alive = False
			printM('Exiting.', self.sender)
			sys.exit()
		elif 'ALARM' in str(d):
			return d
		else:
			if rs.getCHN(d) in self.chans:
				self.raw = rs.update_stream(
					stream=self.raw, d=d, fill_value=None)
				return True
			else:
				return False



	def _deconvolve(self):
		'''
		Deconvolves the stream associated with this class.
		'''
		if self.deconv:
			helpers.deconvolve(self)

	def _get_max_channel_data(self, deconv_channel):
		'''
		deconv_channel can either be acceleration (ACC) or displacement (DISP)
		:rtype: (float, str)
		:return: the maximum peak value for the deconv_channel asked
		'''
		# copy the data
		self.stream = self.raw.copy()
		orig_deconv = self.deconv

		# perform calculations
		self.deconv = deconv_channel
		self._deconvolve()

		# default value
		peakValue = 0
		peakChannel = ""
		for trace in self.stream:
			if trace.stats.channel == "EHZ":
				continue
			tempMax = max(abs(trace.data))
			if tempMax > peakValue:
				peakValue = tempMax
				peakChannel = trace.stats.channel

		# reset the data
		self.stream = self.raw.copy()
		self.deconv = orig_deconv

		# return max value and its channel
		return (peakValue, peakChannel)

	def _when_alarm(self, d):

		n = 0
		while n > 3:
			self.getq()
			n += 1

		n = 0


		while True:
			self.raw = rs.copy(self.raw)
			self.stream = self.raw.copy()

			# compute max acceleration
			(max_pga, max_pga_channel) = self._get_max_channel_data("ACC")

			# compute max displacement
			(max_pgd, max_pgd_channel) = self._get_max_channel_data("DISP")

			# inherit the event_time of the ``ALERT`` that, in turn, triggered the ``PROCESS`` event
			event_time = helpers.fsec(helpers.get_msg_time(d))

			# values to be passed along ``PROCESS`` message
			processed_dict = {
				"max_pga": max_pga,
				"max_pgd": max_pgd,
				"max_pga_channel": max_pga_channel,
				"max_pgd_channel": max_pgd_channel,
				"event_time": str(event_time)
			}

			# raise a flag that the Producer can read and modify
			self.process = json.dumps(processed_dict)
			max_intensity_str = helpers.g_to_intensity(max_pga/G_ACC)

			printM(COLOR["red"] + "Intensity: {0}".format(max_intensity_str) + COLOR["white"] , self.sender)
			cm_disp = max_pgd * 100
			cm_acc = max_pga * 100

			try:
				printM(COLOR["red"] + "Peak displacement is {0:.3g} centimeters along ".format(cm_disp) + max_pgd_channel
						+", and peak acceleration is {0:.3g} centimeters-per-second-squared along ".format(cm_acc)
						+ max_pga_channel + COLOR["white"], self.sender)
			except Exception as e:
				print(cm_disp)
				print(cm_acc)
				print(e)

			sys.stdout.flush()

			if self.testing:
				TEST['c_process'][1] = True

			break


	def run(self):
		'''
		Reads data from the queue and sends a message if it sees an ALARM or IMGPATH message
		'''
		printM("process module ongoing",self.sender)
		while True:
			d = self.getq()

			if 'ALARM' in str(d):
				printM("process module triggered", self.sender)
				self._when_alarm(d)