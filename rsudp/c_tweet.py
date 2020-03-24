import os, sys, platform
import pkg_resources as pr
import time
import math
import numpy as np
from datetime import datetime, timedelta
import rsudp.raspberryshake as rs
from rsudp import printM, printW, printE, helpers
import rsudp
from twython import Twython


class Tweeter(rs.ConsumerThread):
	'''
	 .. versionadded:: 0.4.1

	.. |raspishakeq| raw:: html

		<a href="https://twitter.com/raspishakeq" target="_blank">Raspberry Shake</a>

	.. |usgsbigquakes| raw:: html

		<a href="https://twitter.com/USGSBigQuakes" target="_blank">USGS</a>

	.. |emsc_lastquake| raw:: html

		<a href="https://twitter.com/LastQuake" target="_blank">EMSC</a>

	Twitter is a social media platform sometimes used for quickly
	distributing public alert information. It is used by many agencies
	including |raspishakeq|, |usgsbigquakes|, and |emsc_lastquake|.

	.. |tw_api_bots| raw:: html

		<a href="https://developer.twitter.com/apps" target="_blank">API bots</a>

	.. note::
		Twitter is more difficult and stricter when it comes to making
		|tw_api_bots| than many services.
		First, you must go through a relatively rigorous process of applying for
		a developer account, then making a Twitter "app", and then giving the app
		permission to post on your behalf. See :ref:`setting-up-twitter` for details.

		Once you've gone through that process, Twitter limits posting and makes
		its rules on rate limiting relatively difficult to nail down.
		Generally, the early 2020 rate limit for posting is 300 in a 3-hour span,
		however that can vary depending on whether or not Twitter thinks there is
		suspicious activity coming from your account.

		In general, if you are looking for a simple multi-platform notification
		service, it may be easier and more reliable to use the Telegram service
		instead. rsudp has a telegram module at
		:py:class:rsudp.c_telegram.Telegram:. See :ref:`setting-up-telegram` for details.

	:param str consumer_key: Twitter calls this the "consumer key"
	:param str consumer_secret: Twitter calls this the "consumer key secret"
	:param str access_token: Twitter calls this the "consumer access token"
	:param str access_secret: Twitter calls this the "consumer access secret"
	:param bool send_images: whether or not to send images. if False, only alerts will be sent.
	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`


	'''
	def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret,
				 q=False, tweet_images=False,
				 ):
		"""
		Initialize the process
		"""
		super().__init__()
		self.sender = 'Tweeter'
		self.alive = True
		self.tweet_images = tweet_images
		self.fmt = '%Y-%m-%d %H:%M:%S.%f'
		self.region = ' - region: %s' % rs.region.title() if rs.region else ''
		self.consumer_key = consumer_key
		self.consumer_secret = consumer_secret
		self.access_token = access_token
		self.access_token_secret = access_token_secret

		if q:
			self.queue = q
		else:
			printE('no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			self.alive = False
			sys.exit()

		self.twitter = Twython(
			consumer_key,
			consumer_secret,
			access_token,
			access_token_secret
		)
		self.livelink = 'live feed ➡️ https://raspberryshake.net/stationview/#?net=%s&sta=%s' % (rs.net, rs.stn)
		self.message0 = '(#RaspberryShake station %s.%s%s) Event detected at' % (rs.net, rs.stn, self.region)
		self.message1 = '(#RaspberryShake station %s.%s%s) Image of event detected at' % (rs.net, rs.stn, self.region)

		printM('Starting.', self.sender)
	
	def auth(self):
		self.twitter = Twython(
			self.consumer_key,
			self.consumer_secret,
			self.access_token,
			self.access_token_secret
		)


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
		Send a tweet when you get an ``ALARM`` message.

		:param bytes d: queue message
		'''
		event_time = helpers.fsec(helpers.get_msg_time(d))
		self.last_event_str = '%s' % (event_time.strftime(self.fmt)[:22])
		message = '%s %s UTC - %s' % (self.message0, self.last_event_str, self.livelink)
		response = None
		try:
			printM('Sending tweet...', sender=self.sender)
			response = self.twitter.update_status(status=message, lat=rs.inv[0][0].latitude,
													long=rs.inv[0][0].longitude,
													geo_enabled=True, display_coordinates=True)
													# location will only stick to tweets on accounts that have location enabled in Settings
			printM('Tweeted: %s' % (message), sender=self.sender)
			url = 'https://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id_str'])
			printM('Tweet URL: %s' % url)

		except Exception as e:
			printE('could not send alert tweet - %s' % (e))
			try:
				printE('Waiting 5 seconds and trying to send tweet again...', sender=self.sender, spaces=True)
				time.sleep(5.1)
				self.auth()
				response = self.twitter.update_status(status=message, lat=rs.inv[0][0].latitude,
														long=rs.inv[0][0].longitude,
														geo_enabled=True, display_coordinates=True)
														# location will only stick to tweets on accounts that have location enabled in Settings
				printM('Tweeted: %s' % (message), sender=self.sender)
				url = 'https://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id_str'])
				printM('Tweet URL: %s' % url)
			except Exception as e:
				printE('could not send alert tweet - %s' % (e))
				response = None


	def _when_img(self, d):
		'''
		Send a tweet with an image in when you get an ``IMGPATH`` message.

		:param bytes d: queue message
		'''
		if self.tweet_images:
			imgpath = helpers.get_msg_path(d)
			imgtime = helpers.fsec(helpers.get_msg_time(d))
			message = '%s %s UTC' % (self.message1, imgtime.strftime(self.fmt)[:22])
			response = None
			if os.path.exists(imgpath):
				with open(imgpath, 'rb') as image:
					try:
						printM('Uploading image to Twitter %s' % (imgpath), self.sender)
						response = self.twitter.upload_media(media=image)
						time.sleep(5.1)
						printM('Sending tweet...', sender=self.sender)
						response = self.twitter.update_status(status=message, media_ids=response['media_id'],
																lat=rs.inv[0][0].latitude, long=rs.inv[0][0].longitude,
																geo_enabled=True, display_coordinates=True)
																# location will only stick to tweets on accounts that have location enabled in Settings
						printM('Tweeted with image: %s' % (message), sender=self.sender)
						url = 'https://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id_str'])
						printM('Tweet URL: %s' % url)
					except Exception as e:
						printE('could not send multimedia tweet - %s' % (e))
						try:
							printM('Waiting 5 seconds and trying to send tweet again...', sender=self.sender)
							time.sleep(5.1)
							self.auth()
							printM('Uploading image to Twitter (2nd try) %s' % (imgpath), self.sender)
							response = self.twitter.upload_media(media=image)
							time.sleep(5.1)
							printM('Sending tweet...', sender=self.sender)
							response = self.twitter.update_status(status=message, media_ids=response['media_id'],
																	lat=rs.inv[0][0].latitude, long=rs.inv[0][0].longitude,
																	geo_enabled=True, display_coordinates=True)
																	# location will only stick to tweets on accounts that have location enabled in Settings
							printM('Tweeted with image: %s' % (message), sender=self.sender)
							url = 'https://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id_str'])
							printM('Tweet URL: %s' % url)

						except Exception as e:
							printE('could not send multimedia tweet (2nd try) - %s' % (e))
							response = None

			else:
				printM('Could not find image: %s' % (imgpath), sender=self.sender)


	def run(self):
		"""
		Reads data from the queue and tweets a message if it sees an ALARM or IMGPATH message
		"""
		while True:
			d = self.getq()

			if 'ALARM' in str(d):
				self._when_alarm(d)

			elif 'IMGPATH' in str(d):
				self._when_img(d)
