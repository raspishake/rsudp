import os, sys
import time
import rsudp.raspberryshake as rs
from rsudp import printM, printW, printE, helpers
from rsudp.test import TEST
import telegram as tg

class Telegrammer(rs.ConsumerThread):
	'''
	 .. versionadded:: 0.4.2

	.. |telegram| raw:: html

		<a href="https://t.me/" target="_blank">Telegram</a>

	.. |sasmex_use| raw:: html

		<a href="https://t.me/sasmex" target="_blank">Mexican Early Warning System (SASMEX)</a>

	|telegram| is a free messaging service which,
	among other things, is suited to quickly broadcasting automatic
	notifications via an API.
	It is used by the |sasmex_use| and PanamaIGC.

	:param str token: bot token from Telegram bot creation
	:param str chat_id: Telegram chat ID number that this module will post to
	:param bool send_images: whether or not to send images. if False, only alerts will be sent.
	:type extra_text: bool or str
	:param extra_text: Approximately 3900 additional characters to post as part of the Telegram message (Telegram message limits are 4096 characters). Longer messages will be truncated.
	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`

	'''
	def __init__(self, token, chat_id, testing=False,
				 q=False, send_images=False, extra_text=False,
				 sender='Telegram'):
		"""
		Initializing the Telegram message posting thread.

		"""
		super().__init__()
		self.queue = q
		self.sender = sender
		self.alive = True
		self.send_images = send_images
		self.token = token
		self.chat_id = chat_id
		self.testing = testing
		self.fmt = '%Y-%m-%d %H:%M:%S.%f'
		self.region = ' - region: %s' % rs.region.title() if rs.region else ''

		self.extra_text = helpers.resolve_extra_text(extra_text, max_len=4096, sender=self.sender)

		self.auth()

		self.livelink = u'live feed ➡️ https://stationview.raspberryshake.org/#?net=%s&sta=%s' % (rs.net, rs.stn)
		self.message0 = '(Raspberry Shake station %s.%s%s) Event detected at' % (rs.net, rs.stn, self.region)
		self.last_message = False

		printM('Starting.', self.sender)


	def auth(self):
		if not self.testing:
			self.telegram = tg.Bot(token=self.token)
		else:
			printW('The Telegram module will not post to Telegram in Testing mode.',
					self.sender, announce=False)


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
		message = '%s %s UTC%s - %s' % (self.message0, self.last_event_str, self.extra_text, self.livelink)
		response = None
		try:
			printM('Sending alert...', sender=self.sender)
			printM('Telegram message: %s' % (message), sender=self.sender)
			if not self.testing:
				response = self.telegram.sendMessage(chat_id=self.chat_id, text=message)
			else:
				TEST['c_telegram'][1] = True

		except Exception as e:
			printE('Could not send alert - %s' % (e))
			try:
				printE('Waiting 5 seconds and trying to send again...', sender=self.sender, spaces=True)
				time.sleep(5)
				self.auth()
				printM('Telegram message: %s' % (message), sender=self.sender)
				if not self.testing:
					response = self.telegram.sendMessage(chat_id=self.chat_id, text=message)
				else:
					# if you are here in testing mode, there is a problem
					TEST['c_telegram'][1] = False
			except Exception as e:
				printE('Could not send alert - %s' % (e))
				response = None
		self.last_message = message


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
						if not self.testing:
							printM('Uploading image to Telegram %s' % (imgpath), self.sender)
							response = self.telegram.sendPhoto(chat_id=self.chat_id, photo=image)
							printM('Sent image', sender=self.sender)
						else:
							printM('Image ready to send - %s' % (imgpath), self.sender)
							TEST['c_telegramimg'][1] = True
					except Exception as e:
						printE('Could not send image - %s' % (e))
						try:
							if not self.testing:
								printM('Waiting 5 seconds and trying to send again...', sender=self.sender)
								time.sleep(5.1)
								self.auth()
								printM('Uploading image to Telegram (2nd try) %s' % (imgpath), self.sender)
								response = self.telegram.sendPhoto(chat_id=self.chat_id, photo=image)
								printM('Sent image', sender=self.sender)
							else:
								# if you are here in testing mode, there is a problem
								TEST['c_telegramimg'][1] = False
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
