from datetime import datetime, timedelta

def printM(msg, sender=''):
	'''Prints messages with datetime stamp.'''
	msg = '[%s] %s' % (sender, msg) if sender != '' else msg
	print('%s %s' % (datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), msg))
