import sys, os
from rsudp import printM, printW, printE
from rsudp.raspberryshake import ConsumerThread
from rsudp.test import TEST


class Custom(ConsumerThread):
	"""
	.. versionadded:: 0.4.3

	.. |lineendings_howto| raw:: html

		<a href="https://stackoverflow.com/questions/17579553/windows-command-to-convert-unix-line-endings" target="_blank">this stackoverflow question</a>

	.. |lineendings_wiki| raw:: html

		<a href="https://en.wikipedia.org/wiki/Newline" target="_blank">here</a>

	.. role:: json(code)
		:language: json


	A consumer class that runs custom code from a python file passed to it.
	Please read the disclaimers and warnings at :ref:`customcode` prior to using this module.

	.. warning::

		If you are running Windows and have code you want to pass to the :py:func:`exec` function,
		Python requires that your newline characters are in the UNIX style (:code:`\\n`),
		not the standard Windows style (:code:`\\r\\n`).
		To convert, follow the instructions in one of the answers to |lineendings_howto|.
		If you're not sure what this means, please read about newline/line ending characters |lineendings_wiki|.
		If you are certain that your code file has no Windows newlines, you can set :json:`"win_override"` to true.

		Read more warnings about this module at :ref:`customcode`.

	:param queue.Queue q: queue of data and messages sent by :class:`rsudp.c_consumer.Consumer`.
	:param codefile: string of the python (.py) file to run, or False if none.
	:type codefile: str or bool
	:param bool win_ovr: user check to make sure that line ending format is correct (see warning above)

	"""

	def __init__(self, q=False, codefile=False, win_ovr=False, testing=False):
		"""
		Initializes the custom code execution thread.
		"""
		super().__init__()
		self.sender = 'Custom'
		self.alive = True
		self.testing = testing
		self.codefile = False
		self.win_ovr = win_ovr
		if codefile:
			if (os.path.exists(os.path.expanduser(codefile))) and (os.path.splitext(codefile)[1]):
				self.codefile = os.path.expanduser(codefile)
				printM('Custom code file to run: %s' % self.codefile, sender=self.sender)
			else:
				printW('No python file exists at %s. No custom code will be run during alarms.' % codefile, sender=self.sender)
		else:
			printW('No custom code file set. No custom code will be run during alarms.', sender=self.sender)

		if (os.name in 'nt') and (not self.win_ovr):
			printE('Using Windows with custom alert code! Your code MUST have UNIX/Mac newline characters!')
			printE('Please use a conversion tool like dos2unix to convert line endings', spaces=True)
			printE('(https://en.wikipedia.org/wiki/Unix2dos) to make your code file', spaces=True)
			printE('readable to the Python interpreter.', spaces=True)
			printE('Once you have done that, please set "win_override" to true', spaces=True)
			printE('in the settings file.', spaces=True)
			printE('(see also footnote [1] on this page: https://docs.python.org/3/library/functions.html#id2)', spaces=True)
			printE('THREAD EXITING, please correct and restart!', self.sender, spaces=True)
			sys.exit(2)
		else:
			pass


		if q:
			self.queue = q
		else:
			printE('no queue passed to the consumer thread! We will exit now!',
				   self.sender)
			sys.stdout.flush()
			self.alive = False
			sys.exit()

		printM('Starting.', self.sender)

	def exec_code(self):
		if self.codefile:
			# if the user has set a code file
			printM('Executing code from file: %s' % self.codefile, sender=self.sender)
			try:
				# try to execute some code
				exec(self.codefile)
				if self.testing:
					TEST['c_custom'][1] = True
			except Exception as e:
				# do something if it fails
				printE('Code execution failed. Error: %s' % e, sender=self.sender, announce=False)
		else:
			printW('No code to run, codefile variable not set correctly.', sender=self.sender)


	def run(self):
		"""
		Reads data from the queue and executes self.codefile if it sees an ``ALARM`` message.
		Quits if it sees a ``TERM`` message.
		"""
		while True:
			d = self.queue.get()
			self.queue.task_done()
			if 'TERM' in str(d):
				self.alive = False
				printM('Exiting.', self.sender)
				sys.exit()
			elif 'ALARM' in str(d):
				printM('Got ALARM message...', sender=self.sender)
				self.exec_code()

		self.alive = False
