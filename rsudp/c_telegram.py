import os, sys
import time
from threading import Thread
from datetime import datetime, timedelta
import rsudp.raspberryshake as RS
from rsudp import printM
import rsudp
import telegram as tg

class Telegrammer(Thread):
	'''
	 .. versionadded:: 0.4.2

	`Telegram <https://t.me/>`_ is a free messaging service which,
	among other things, is suited to quickly broadcasting automatic
	notifications via an API.
	It is `used <https://t.me/sasmex>`_ by the Mexican Early Warning
	System (SASMEX) and PanamaIGC.

	
	'''
	def __init__(self, token, chat_id,
				 q=False, send_images=False,
				 ):
		"""
		Initializing the Telegram message posting thread.

		:param str token: bot token from Telegram bot creation
		:param str chat_id: Telegram chat ID number that this module will post to
		:param bool send_images: whether or not to send images. if False, only alerts will be sent.
		:param queue.Queue q: queue of data and messages sent by :class:`rsudp.p_producer.Producer`

		"""
		super().__init__()
		self.sender = 'Telegram'
		self.alarm = False
		self.alive = True
		self.send_images = send_images
		self.token = token
		self.chat_id = chat_id
		self.fmt = '%Y-%m-%d %H:%M:%S UTC'
		self.region = ' - region: %s' % RS.region.title() if RS.region else ''

		if q:
			self.queue = q
		else:
			printM('ERROR: no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			self.alive = False
			sys.exit()

		self.telegram = tg.Bot(token=self.token)

		self.livelink = 'live feed ➡️ https://raspberryshake.net/stationview/#?net=%s&sta=%s' % (RS.net, RS.stn)
		self.message0 = '(Raspberry Shake station %s.%s%s) Event detected at' % (RS.net, RS.stn, self.region)

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

	def run(self):
		"""
		Reads data from the queue and sends a message if it sees an ALARM or IMGPATH message
		"""
		while True:
			d = self.getq()

			if 'ALARM' in str(d):
				event_time = RS.UTCDateTime.strptime(d.decode('utf-8'), 'ALARM %Y-%m-%dT%H:%M:%S.%fZ')
				self.last_event_str = event_time.strftime(self.fmt)
				message = '%s %s - %s' % (self.message0, self.last_event_str, self.livelink)
				response = None
				try:
					printM('Sending alert...', sender=self.sender)
					response = self.telegram.sendMessage(chat_id=self.chat_id, text=message)
					print()
					printM('Sent Telegram: %s' % (message), sender=self.sender)

				except Exception as e:
					printM('ERROR: could not send alert - %s' % (e))
					try:
						printM('Waiting 5 seconds and trying to send again...', sender=self.sender)
						time.sleep(5)
						self.auth()
						response = self.telegram.sendMessage(chat_id=self.chat_id, text=message)
						print()
						printM('Sent Telegram: %s' % (message), sender=self.sender)
					except Exception as e:
						printM('ERROR: could not send alert - %s' % (e))
						response = None


			elif 'IMGPATH' in str(d):
				if self.send_images:
					imgdetails = d.decode('utf-8').split(' ')
					response = None
					print()
					if os.path.exists(imgdetails[2]):
						with open(imgdetails[2], 'rb') as image:
							try:
								printM('Uploading image to Telegram %s' % (imgdetails[2]), self.sender)
								response = self.telegram.sendPhoto(chat_id=self.chat_id, photo=image)
								print()
								printM('Sent image', sender=self.sender)
							except Exception as e:
								printM('ERROR: could not send photo - %s' % (e))
								try:
									printM('Waiting 5 seconds and trying to send again...', sender=self.sender)
									time.sleep(5.1)
									self.auth()
									printM('Uploading image to Telegram (2nd try) %s' % (imgdetails[2]), self.sender)
									response = self.telegram.sendPhoto(chat_id=self.chat_id, photo=image)
									print()
									printM('Sent image', sender=self.sender)

								except Exception as e:
									printM('ERROR: could not send alert - %s' % (e))
									response = None

					else:
						printM('Could not find image: %s' % (imgdetails[2]), sender=self.sender)
