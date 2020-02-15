import os, sys, platform
import pkg_resources as pr
import time
import math
from threading import Thread
import numpy as np
from datetime import datetime, timedelta
import rsudp.raspberryshake as RS
from rsudp import printM
import rsudp
from twython import Twython


class Tweeter(Thread):
	def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret,
				 q=False, tweet_images=False,
				 ):
		"""
		Initialize the process
		"""
		super().__init__()
		self.sender = 'Tweeter'
		self.alarm = False
		self.alive = True
		self.tweet_images = tweet_images
		self.fmt = '%Y-%m-%d %H:%M:%S UTC'
		self.region = ' - region: %s' % RS.region.title() if RS.region else ''
		self.consumer_key = consumer_key
		self.consumer_secret = consumer_secret
		self.access_token = access_token
		self.access_token_secret = access_token_secret

		if q:
			self.queue = q
		else:
			printM('ERROR: no queue passed to consumer! Thread will exit now!', self.sender)
			sys.stdout.flush()
			self.alive = False
			sys.exit()

		self.twitter = Twython(
			consumer_key,
			consumer_secret,
			access_token,
			access_token_secret
		)
		self.livelink = 'live feed ➡️ https://raspberryshake.net/stationview/#?net=%s&sta=%s' % (RS.net, RS.stn)
		self.message0 = '(#RaspberryShake station %s.%s%s) Event detected at' % (RS.net, RS.stn, self.region)
		self.message1 = '(#RaspberryShake station %s.%s%s) Image of event detected at' % (RS.net, RS.stn, self.region)

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

	def run(self):
		"""
		Reads data from the queue and tweets a message if it sees an ALARM or IMGPATH message
		"""
		while True:
			d = self.getq()

			if 'ALARM' in str(d):
				event_time = RS.UTCDateTime.strptime(d.decode('utf-8'), 'ALARM %Y-%m-%dT%H:%M:%S.%fZ')
				self.last_event_str = event_time.strftime(self.fmt)
				message = '%s %s - %s' % (self.message0, self.last_event_str, self.livelink)
				response = None
				try:
					printM('Sending tweet...', sender=self.sender)
					response = self.twitter.update_status(status=message, lat=RS.inv[0][0].latitude,
														  long=RS.inv[0][0].longitude,
														  geo_enabled=True, display_coordinates=True)
														  # location will only stick to tweets on accounts that have location enabled in Settings
					print()
					printM('Tweeted: %s' % (message), sender=self.sender)
					url = 'https://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id_str'])
					printM('Tweet URL: %s' % url)

				except Exception as e:
					printM('ERROR: could not send alert tweet - %s' % (e))
					try:
						printM('Waiting 5 seconds and trying to send tweet again...', sender=self.sender)
						time.sleep(5.1)
						self.auth()
						response = self.twitter.update_status(status=message, lat=RS.inv[0][0].latitude,
															  long=RS.inv[0][0].longitude,
															  geo_enabled=True, display_coordinates=True)
															  # location will only stick to tweets on accounts that have location enabled in Settings
						print()
						printM('Tweeted: %s' % (message), sender=self.sender)
						url = 'https://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id_str'])
						printM('Tweet URL: %s' % url)
					except Exception as e:
						printM('ERROR: could not send alert tweet - %s' % (e))
						response = None


			elif 'IMGPATH' in str(d):
				if self.tweet_images:
					imgdetails = d.decode('utf-8').split(' ')
					imgtime = RS.UTCDateTime.strptime(imgdetails[1], '%Y-%m-%dT%H:%M:%S.%fZ')
					message = '%s %s' % (self.message1, imgtime.strftime(self.fmt))
					response = None
					print()
					if os.path.exists(imgdetails[2]):
						with open(imgdetails[2], 'rb') as image:
							try:
								printM('Uploading image to Twitter %s' % (imgdetails[2]), self.sender)
								response = self.twitter.upload_media(media=image)
								print()
								time.sleep(5.1)
								printM('Sending tweet...', sender=self.sender)
								response = self.twitter.update_status(status=message, media_ids=response['media_id'],
																	  lat=RS.inv[0][0].latitude, long=RS.inv[0][0].longitude,
																	  geo_enabled=True, display_coordinates=True)
																	  # location will only stick to tweets on accounts that have location enabled in Settings
								print()
								printM('Tweeted with image: %s' % (message), sender=self.sender)
								url = 'https://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id_str'])
								printM('Tweet URL: %s' % url)
							except Exception as e:
								printM('ERROR: could not send multimedia tweet - %s' % (e))
								try:
									printM('Waiting 5 seconds and trying to send tweet again...', sender=self.sender)
									time.sleep(5.1)
									self.auth()
									printM('Uploading image to Twitter (2nd try) %s' % (imgdetails[2]), self.sender)
									response = self.twitter.upload_media(media=image)
									print()
									time.sleep(5.1)
									printM('Sending tweet...', sender=self.sender)
									response = self.twitter.update_status(status=message, media_ids=response['media_id'],
																		  lat=RS.inv[0][0].latitude, long=RS.inv[0][0].longitude,
																		  geo_enabled=True, display_coordinates=True)
																		  # location will only stick to tweets on accounts that have location enabled in Settings
									print()
									printM('Tweeted with image: %s' % (message), sender=self.sender)
									url = 'https://twitter.com/%s/status/%s' % (response['user']['screen_name'], response['id_str'])
									printM('Tweet URL: %s' % url)

								except Exception as e:
									printM('ERROR: could not send alert tweet - %s' % (e))
									response = None

					else:
						printM('Could not find image: %s' % (imgdetails[2]), sender=self.sender)
