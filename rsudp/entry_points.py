import platform
import subprocess
import os
from rsudp import COLOR, log_loc, settings_loc


def ep_edit_settings():
	'''
	This function calls the system's default text editor to open the settings
	file for editing. It is provided for convenience only.

	This function is accessible via the console command ``rs-settings``.

	Advanced users may prefer to add an alias in place of this function.
	The alias **should** override the entrypoint command set in rsudp's
	``setup.py``.

	On Linux and MacOS, adding an alias may look like this:

	.. code-block:: bash

		# add the alias definition to the aliases file
		echo "alias rsudp-settings='nano ~/.config/rsudp/rsudp_settings.json'" >> .bash_aliases
		# then reload the console
		bash

	To add an alias on Windows via the command prompt is much more difficult,
	so the method is not provided here.

	.. note::

		This function has been tested on multiple operating systems, but
		because each system's functionality and defaults may be different,
		proper operation cannot be not guaranteed.

	'''
	if not os.path.exists(settings_loc):
		raise(FileNotFoundError('Settings file not found at %s' % settings_loc))

	if platform.system() == 'Darwin':		# MacOS
		subprocess.call(('open', settings_loc))
	elif platform.system() == 'Windows':	# Windows
		os.startfile(settings_loc)
	else:									# linux variants
		subprocess.call(('xdg-open', settings_loc))

def ep_cat_log():
	'''
	This function uses a posix system's ``cat`` command to print messages in
	the rsudp log file. It is provided for convenience only.

	It is accessible via the console command ``rs-log`` on posix (Linux, MacOS)
	style operating systems.

	.. note::

		This function is the equivalent of ``cat /tmp/rsudp/rsudp.log`` on
		Linux/MacOS and ``type "C:/tmp/rsudp/rsudp.log"`` on
		Windows.
	'''
	if os.name == 'posix':
		subprocess.call(('cat', log_loc))
	else:
		subprocess.call(('type', '"' + log_loc + '"'))

def ep_tailf_log():
	'''
	This function uses a the system's follow command to follow new
	messages added to the log file. It is provided for convenience only.

	This function is accessible via the console command ``rs-tailf``.

	The function will run until it receives a keyboard interrupt
	(:kbd:`Ctrl`\ +\ :kbd:`C`).

	.. note::

		This function is the equivalent of ``tail -f /tmp/rsudp/rsudp.log`` on
		Linux/MacOS and ``Get-Content -Path "C:/tmp/rsudp/rsudp.log" -Wait`` on
		Windows.

	'''
	if os.name == 'posix':
		try:
			print(COLOR['blue'] + 'Entering log follow (tail -f) mode.')
			print('New log messages will be printed until the console receives an interrupt (CTRL+C to end).' + COLOR['white'])
			subprocess.call(('tail','-f', log_loc))
		except KeyboardInterrupt:
			print()
			print(COLOR['blue'] + 'Quitting tail -f mode.' + COLOR['white'])
	if os.name == 'nt':
		try:
			print('Entering log follow mode.')
			print('New log messages will be printed until the console receives an interrupt (CTRL+C to end).')
			subprocess.call(('Get-Content', '-Path', '"' + log_loc + '"', '-Wait'))
		except Exception as e:
			print('This function is not available on Windows. Error: %s' % (e))
