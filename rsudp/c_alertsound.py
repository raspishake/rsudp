import sys, os
from rsudp.raspberryshake import ConsumerThread
from rsudp import printM, printW, printE, helpers
from rsudp.test import TEST
from gtts import gTTS
from io import BytesIO

import subprocess
try:
	from pydub.playback import play
	from pydub import AudioSegment, utils
	pydub_exists = True
	# avoids import error that arises between pydub 0.23.1 and 0.25.1
	global PLAYER
	PLAYER = utils.get_player_name()
	TEST['d_pydub'][1] = True
except ImportError as e:
	global ERR
	ERR = e
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

	def _load_sound(self, soundloc):
		'''
		Loads MP3 sound if possible, then writes to wav.
		Catches a ``FileNotFoundError`` when no player can be loaded.
		'''
		try:
			self.sound = AudioSegment.from_file(soundloc, format="mp3")
			printM('Loaded %.2f sec alert sound from %s' % (len(self.sound)/1000., soundloc), sender=self.sender)
			self.wavloc = '%s.wav' % os.path.splitext(soundloc)[0]
			if 'ffplay' in PLAYER:
				self._write_wav()
		except FileNotFoundError as e:
			printE('Error loading player - %s' % (e), sender=self.sender)
			printW("You have chosen to play a sound, but don't have ffmpeg or libav installed.", sender=self.sender)
			printW('Sound playback requires one of these dependencies.', sender=self.sender, spaces=True)
			printW("To install either dependency, follow the instructions at:", sender=self.sender, spaces=True)
			printW('https://github.com/jiaaro/pydub#playback', sender=self.sender, spaces=True)
			printW('The program will now continue without sound playback.', sender=self.sender, spaces=True)
			self.sound = False

	def _init_sound(self, soundloc):
		if pydub_exists:
			if os.path.exists(soundloc):
				self._load_sound(soundloc)
			else:
				printW("The file %s could not be found." % (soundloc), sender=self.sender)
				printW('The program will now continue without sound playback.', sender=self.sender, spaces=True)
				self.sound = False
		else:
			printE('Error importing pydub - %s' % ERR, sender=self.sender)
			printW("You don't have pydub installed, so no sound will play.", sender=self.sender)
			printW('To install pydub, follow the instructions at:', sender=self.sender, spaces=True)
			printW('https://github.com/jiaaro/pydub#installation', sender=self.sender, spaces=True)
			printW('Sound playback also requires you to install either ffmpeg or libav.', sender=self.sender, spaces=True)

	def _write_wav(self):
		'''
		FFPlay can only play raw wav sounds without verbosity, so to support
		non-verbose mode we must export to .wav prior to playing a sound.
		This function checks for an existing wav file and if it does not
		exist, writes a new one.

		However, we'll always rewrite if gtts_enabled (meaning, there's the announcement speech
		is updated all the time)
		'''
		if not os.path.isfile(self.wavloc) or self.gtts_enabled:
			self.sound.export(self.wavloc, format="wav")
			printM('Wrote wav version of sound file %s' % (self.wavloc), self.sender)


	def __init__(self, testing=False, soundloc=False, q=False, gtts_enabled=False, tts_loc=None, is_ground_floor=False):
		"""
		.. _pydub.AudioSegment: https://github.com/jiaaro/pydub/blob/master/API.markdown#audiosegment

		Initializes the alert sound listener thread.
		Needs a pydub.AudioSegment_ to play and a :class:`queue.Queue` to listen on.

		"""
		super().__init__()
		self.sender = 'AlertSound'
		self.alive = True
		self.testing = testing

		self.sound = None
		self.soundloc = soundloc
		self.devnull = open(os.devnull, 'w')

		self.gtts_enabled = gtts_enabled
		self.tts_loc = tts_loc
		self.is_ground_floor = is_ground_floor

		# initialize only once
		if not self.gtts_enabled:
			self._init_sound(soundloc)

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
		self._write_wav()
		subprocess.call([PLAYER,"-nodisp", "-autoexit", "-hide_banner",
						self.wavloc], stdout=self.devnull, stderr=self.devnull)

	def _play(self):
		printM('Playing alert sound...', sender=self.sender)
		if 'ffplay' in PLAYER:
			self._play_quiet()
		else:
			play(self.sound)
		if self.testing:
			TEST['c_play'][1] = True

	def _convert_text_to_speech(self, d):
		'''
		Gets the pga and pgd values from the PROCESS event
		and generates a new sound alert, prepended by the original alert message.
		'''
		max_values_dict = helpers.get_msg_process_values(d)
		pga = max_values_dict['max_pga']
		pgd = max_values_dict['max_pgd']
		alert_text_1 = helpers.get_intensity_alert_text(pga)
		alert_text_2 = helpers.get_pga_pgd_alert_text(pga, pgd)
		announcement = 'Attention!' + (alert_text_1 + alert_text_2 if self.is_ground_floor else alert_text_2)

		speech = gTTS(text=announcement, lang="en", slow=False)

		# Convert the audio data to an in-memory file-like object
		audio_file = BytesIO()
		speech.write_to_fp(audio_file)
		audio_file.seek(0)

		# Load the audio data into pydub
		speech_audio = AudioSegment.from_file(audio_file, format='mp3')

		# The original alarm
		alert_audio = AudioSegment.from_file(self.soundloc, format="mp3")

		# combine_audio
		final_tts_audio = alert_audio + speech_audio
		# save audio to file
		final_tts_audio.export(self.tts_loc, format="mp3")

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
				self.devnull.close()
				printM('Exiting.', self.sender)
				sys.exit()
			elif 'PROCESS' in str(d):

				if self.gtts_enabled:
					self._convert_text_to_speech(d)
					self._init_sound(self.tts_loc)

				if self.sound and pydub_exists:
					self._play()
