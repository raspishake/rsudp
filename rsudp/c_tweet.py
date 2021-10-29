import os, sys
import time
import rsudp.raspberryshake as rs
from rsudp import printM, printW, printE, helpers
from rsudp.test import TEST
from twython import Twython


class Tweeter(rs.ConsumerThread):
	'''
	.. versionadded:: 1.0.2

		The option to add extra text to tweets using the :code:`"extra_text"`
		setting in settings files built by this version and later.

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
		:py:class:`rsudp.c_telegram.Telegram`. See :ref:`setting-up-telegram` for details.

	:param str consumer_key: Twitter calls this the "consumer key"
	:param str consumer_secret: Twitter calls this the "consumer key secret"
	:param str access_token: Twitter calls this the "consumer access token"
	:param str access_secret: Twitter calls this the "consumer access secret"
	:param bool tweet_images: whether or not to send images. if False, only alerts will be sent.
	:type extra_text: bool or str
	:param extra_text: 103 additional characters to post as part of the twitter message (longer messages will be truncated).
	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`


	'''
	def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret,
				 q=False, tweet_images=False, extra_text=False, testing=False,
				 ):
		"""
		Initialize the process
		"""
		super().__init__()
		self.queue = q
		self.sender = 'Tweeter'
		self.alive = True
		self.tweet_images = tweet_images
		self.testing = testing
		self.fmt = '%Y-%m-%d %H:%M:%S.%f'
		self.region = ' - region: %s' % rs.region.title() if rs.region else ''
		self.consumer_key = consumer_key
		self.consumer_secret = consumer_secret
		self.access_token = access_token
		self.access_token_secret = access_token_secret
		self.last_message = False

		self.extra_text = helpers.resolve_extra_text(extra_text, max_len=280, sender=self.sender)

		self.auth()

		self.livelink = u'live feed ➡️ https://stationview.raspberryshake.org/#?net=%s&sta=%s' % (rs.net, rs.stn)
		self.message0 = '(#RaspberryShake station %s.%s%s) Event detected at' % (rs.net, rs.stn, self.region)
		self.message1 = '(#RaspberryShake station %s.%s%s) Image of event detected at' % (rs.net, rs.stn, self.region)

		printM('Starting.', self.sender)


	def auth(self):
		if not self.testing:
			self.twitter = Twython(
				self.consumer_key,
				self.consumer_secret,
				self.access_token,
				self.access_token_secret
			)
		else:
			printW('The Twitter module will not post to Twitter in Testing mode.',
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
		Send a tweet when you get an ``ALARM`` message.

		:param bytes d: queue message
		'''
		event_time = helpers.fsec(helpers.get_msg_time(d))
		self.last_event_str = '%s' % (event_time.strftime(self.fmt)[:22])
		message = '%s %s UTC%s - %s' % (self.message0, self.last_event_str, self.extra_text, self.livelink)
		response = None
		try:
			printM('Tweet: %s' % (message), sender=self.sender)
			if not self.testing:
				response = self.twitter.update_status(status=message, lat=rs.inv[0][0].latitude,
														long=rs.inv[0][0].longitude,
														geo_enabled=True, display_coordinates=True)
														# location will only stick to tweets on accounts that have location enabled in Settings
				url = 'https://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id_str'])
				printM('Tweet URL: %s' % url)
			if self.testing:
				TEST['c_tweet'][1] = True

		except Exception as e:
			printE('could not send alert tweet - %s' % (e))
			try:
				printE('Waiting 5 seconds and trying to send tweet again...', sender=self.sender, spaces=True)
				time.sleep(5.1)
				printM('Tweet: %s' % (message), sender=self.sender)
				if not self.testing:
					self.auth()
					response = self.twitter.update_status(status=message, lat=rs.inv[0][0].latitude,
															long=rs.inv[0][0].longitude,
															geo_enabled=True, display_coordinates=True)
															# location will only stick to tweets on accounts that have location enabled in Settings
					url = 'https://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id_str'])
					printM('Tweet URL: %s' % url)
			except Exception as e:
				printE('could not send alert tweet - %s' % (e))
				response = None

		self.last_message = message



	def _when_img(self, d):
		'''
		Send a tweet with an image in when you get an ``IMGPATH`` message.

		:param bytes d: queue message
		'''
		if self.tweet_images:
			imgpath = helpers.get_msg_path(d)
			imgtime = helpers.fsec(helpers.get_msg_time(d))
			message = '%s %s UTC%s' % (self.message1, imgtime.strftime(self.fmt)[:22], self.extra_text)
			response = None
			printM('Image tweet: %s' % (message), sender=self.sender)
			if not self.testing:
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
								url = 'https://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id_str'])
								printM('Tweet URL: %s' % url)

							except Exception as e:
								printE('could not send multimedia tweet (2nd try) - %s' % (e))
								response = None

				else:
					printM('Could not find image: %s' % (imgpath), sender=self.sender)
			else:
				TEST['c_tweetimg'][1] = True
		
		self.last_message = message

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
