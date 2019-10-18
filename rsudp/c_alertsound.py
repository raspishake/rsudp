import sys
from threading import Thread
from rsudp import printM
try:
	from pydub.playback import play
	pydub_exists = True
except ImportError:
	pydub_exists = False


class AlertSound(Thread):
	"""
	A sub-consumer class that simply prints incoming data to the terminal.
	This is enabled by setting the "printdata" > "enabled" parameter to `true`
	in the settings file. This is more of a debug feature than anything else,
	meant to be a way to check that data is flowing into the port.


	"""

	def __init__(self, sound=False, q=False):
		"""
		Initialize the process
		"""
		super().__init__()
		self.sender = 'AlertSound'
		self.alarm = False
		self.alive = True
		self.sound = sound

		if q:
			self.queue = q
		else:
			printM('ERROR: no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			self.alive = False
			sys.exit()

		printM('Starting.', self.sender)

	def run(self):
		"""
		Reads data from the queue and print to stdout
		"""
		while True:
			d = self.queue.get()
			self.queue.task_done()
			if 'TERM' in str(d):
				sys.exit()
			elif 'ALARM' in str(d):
				printM('Playing alert sound...', sender=self.sender)
				if self.sound and pydub_exists:
					play(self.sound)

				

		self.alive = False