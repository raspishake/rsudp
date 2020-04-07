import os, sys
import time
from datetime import datetime, timedelta
from rsudp.raspberryshake import ConsumerThread
import rsudp.raspberryshake as rs
from rsudp import printM, printW, printE, helpers
import rsudp
import telegram as tg

class Telegrammer(rs.ConsumerThread):
	'''
	 .. versionadded:: 0.4.2

	.. |telegram| raw:: html

		<a href="https://t.me/" target="_blank">Telegram</a>

	.. |sasmex_use| raw:: html

		<a href="https://t.me/sasmex" target="_blank">used by</a>

	|telegram| is a free messaging service which,
	among other things, is suited to quickly broadcasting automatic
	notifications via an API.
	It is |sasmex_use| the Mexican Early Warning
	System (SASMEX) and PanamaIGC.

	:param str token: bot token from Telegram bot creation
	:param str chat_id: Telegram chat ID number that this module will post to
	:param bool send_images: whether or not to send images. if False, only alerts will be sent.
	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`

	'''
	def __init__(self, token, chat_id,
				 q=False, send_images=False,
				 sender='Telegram'):
		"""
		Initializing the Telegram message posting thread.

		"""
		super().__init__()
		self.sender = sender
		self.alive = True
		self.send_images = send_images
		self.token = token
		self.chat_id = chat_id
		self.fmt = '%Y-%m-%d %H:%M:%S.%f'
		self.region = ' - region: %s' % rs.region.title() if rs.region else ''

		if q:
			self.queue = q
		else:
			printE('no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			self.alive = False
			sys.exit()

		self.telegram = tg.Bot(token=self.token)

		self.livelink = 'live feed ➡️ https://raspberryshake.net/stationview/#?net=%s&sta=%s' % (rs.net, rs.stn)
		self.message0 = '(Raspberry Shake station %s.%s%s) Event detected at' % (rs.net, rs.stn, self.region)

		printM('Starting.', self.sender)


	def auth(self):
		self.telegram = tg.Bot(token=self.token)


	def getq(self):
		d = self.queue.get()
		self.queue.task_done()

		if 'TERM' in str(d):
			self.alive = False
			printM('Exiting.', self.sender)
			sys.exit()
		else:
			return d


	def _when_alarm(self, d):
		'''
		Send a telegram in an alert scenario.

		:param bytes d: queue message
		'''
		event_time = helpers.fsec(helpers.get_msg_time(d))
		self.last_event_str = '%s' % (event_time.strftime(self.fmt)[:22])
		message = '%s %s UTC - %s' % (self.message0, self.last_event_str, self.livelink)
		response = None
		try:
			printM('Sending alert...', sender=self.sender)
			response = self.telegram.sendMessage(chat_id=self.chat_id, text=message)
			printM('Sent Telegram: %s' % (message), sender=self.sender)

		except Exception as e:
			printE('Could not send alert - %s' % (e))
			try:
				printE('Waiting 5 seconds and trying to send again...', sender=self.sender, spaces=True)
				time.sleep(5)
				self.auth()
				response = self.telegram.sendMessage(chat_id=self.chat_id, text=message)
				printM('Sent Telegram: %s' % (message), sender=self.sender)
			except Exception as e:
				printE('Could not send alert - %s' % (e))
				response = None


	def _when_img(self, d):
		'''
		Send a telegram image in when you get an ``IMGPATH`` message.

		:param bytes d: queue message
		'''
		if self.send_images:
			imgpath = helpers.get_msg_path(d)
			response = None
			if os.path.exists(imgpath):
				with open(imgpath, 'rb') as image:
					try:
						printM('Uploading image to Telegram %s' % (imgpath), self.sender)
						response = self.telegram.sendPhoto(chat_id=self.chat_id, photo=image)
						printM('Sent image', sender=self.sender)
					except Exception as e:
						printE('Could not send image - %s' % (e))
						try:
							printM('Waiting 5 seconds and trying to send again...', sender=self.sender)
							time.sleep(5.1)
							self.auth()
							printM('Uploading image to Telegram (2nd try) %s' % (imgpath), self.sender)
							response = self.telegram.sendPhoto(chat_id=self.chat_id, photo=image)
							printM('Sent image', sender=self.sender)

						except Exception as e:
							printE('Could not send image - %s' % (e))
							response = None
			else:
				printM('Could not find image: %s' % (imgpath), sender=self.sender)


	def run(self):
		"""
		Reads data from the queue and sends a message if it sees an ALARM or IMGPATH message
		"""
		while True:
			d = self.getq()

			if 'ALARM' in str(d):
				self._when_alarm(d)

			elif 'IMGPATH' in str(d):
				self._when_img(d)
