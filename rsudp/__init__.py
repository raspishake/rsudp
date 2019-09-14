from datetime import datetime, timedelta

def printM(msg, sender=''):
	'''Prints messages with datetime stamp.'''
	msg = '[%s] %s' % (sender, msg) if sender != '' else msg
	print('%s %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg))
