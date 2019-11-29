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
		self.message0 = '(Raspberry Shake station %s.%s) Event detected at' % (RS.net, RS.stn)
		self.message1 = '(Raspberry Shake station %s.%s) Image of event detected at' % (RS.net, RS.stn)

		printM('Starting.', self.sender)
	
	def getq(self):
		d = self.queue.get()
		self.queue.task_done()

		if 'TERM' in str(d):
			self.alive = False
			printM('Exiting.', self.sender)
			sys.exit()

		elif 'ALARM' in str(d):
			event_time = RS.UTCDateTime.strptime(d.decode('utf-8'), 'ALARM %Y-%m-%dT%H:%M:%S.%fZ')
			self.last_event_str = event_time.strftime(self.fmt)
			message = '%s %s' % (self.message0, self.last_event_str)
			printM('Sending tweet...', sender=self.sender)
			self.twitter.update_status(status=message)
			print()
			printM('Tweeted: %s' % (message), sender=self.sender)

		elif 'IMGPATH' in str(d):
			if self.tweet_images:
				imgdetails = d.decode('utf-8').split(' ')
				imgtime = RS.UTCDateTime.strptime(imgdetails[1], '%Y-%m-%dT%H:%M:%S.%fZ')
				message = '%s %s' % (self.message1, imgtime.strftime(self.fmt))
				print()
				if os.path.exists(imgdetails[2]):
					with open(imgdetails[2], 'rb') as image:
						printM('Uploading image to Twitter %s' % (imgdetails[2]), self.sender)
						response = self.twitter.upload_media(media=image)
						print()
						printM('Sending tweet...', sender=self.sender)
						self.twitter.update_status(status=message, media_ids=response['media_id'])
					print()
					printM('Tweeted with image: %s' % (message), sender=self.sender)
				else:
					printM('Could not find image: %s' % (imgdetails[2]), sender=self.sender)

	def run(self):
		"""
		Reads data from the queue and plays self.sound if it sees an ALARM message
		"""
		while True:
			self.getq()