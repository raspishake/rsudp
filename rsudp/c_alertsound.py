import sys, os
from rsudp.raspberryshake import ConsumerThread
from rsudp import printM, printW, printE
import subprocess
from tempfile import NamedTemporaryFile
try:
	from pydub.playback import play, PLAYER
	pydub_exists = True
except ImportError:
	pydub_exists = False


class AlertSound(ConsumerThread):
	"""
	.. _pydub.AudioSegment: https://github.com/jiaaro/pydub/blob/master/API.markdown#audiosegment

	A consumer class that plays an alert sound when an ``ALARM`` message arrives on the queue.
	``rsudp.c_alertsound.AlertSound.sound`` is a pydub.AudioSegment_ object and is passed from the client.

	:param sta: short term average (STA) duration in seconds.
	:type sta: bool or pydub.AudioSegment_ 
	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`.

	"""

	def __init__(self, sound=False, soundloc=False, q=False):
		"""
		.. _pydub.AudioSegment: https://github.com/jiaaro/pydub/blob/master/API.markdown#audiosegment

		Initializes the alert sound listener thread.
		Needs a pydub.AudioSegment_ to play and a :class:`queue.Queue` to listen on.

		"""
		super().__init__()
		self.sender = 'AlertSound'
		self.alive = True
		self.sound = sound
		self.tmpfile = None
		self.devnull = open(os.devnull, 'w')
		self.wavloc = '%s.wav' % os.path.splitext(soundloc)[0]

		if q:
			self.queue = q
		else:
			printE('no queue passed to the consumer thread! We will exit now!',
				   self.sender)
			sys.stdout.flush()
			self.alive = False
			sys.exit()

		printM('Starting.', self.sender)

	def _play_quiet(self):
		'''
		if FFPlay is the player, suppress printed output.
		'''
		if not os.path.isfile(self.wavloc):
			self.sound.export(self.wavloc, format="wav")
			printM('Wrote wav version of sound file %s' % (self.wavloc), self.sender)

		subprocess.call([PLAYER,"-nodisp", "-autoexit", "-hide_banner",
						self.wavloc], stdout=self.devnull, stderr=self.devnull)

	def _play(self):
		if 'ffplay' in PLAYER:
			self._play_quiet()
		else:
			play(self.sound)

	def run(self):
		"""
		Reads data from the queue and plays self.sound if it sees an ``ALARM`` message.
		Quits if it sees a ``TERM`` message.
		"""
		while True:
			d = self.queue.get()
			self.queue.task_done()
			if 'TERM' in str(d):
				self.alive = False
				printM('Exiting.', self.sender)
				sys.exit()
			elif 'ALARM' in str(d):
				printM('Playing alert sound...', sender=self.sender)
				if self.sound and pydub_exists:
					self._play()

		self.alive = False
