import platform
import subprocess
import os
from rsudp import COLOR, log_loc, settings_loc


def ep_edit_settings():
	'''
	.. versionadded:: 1.0.3

	This function calls the system's default text editor to open the settings
	file for editing. It is provided for convenience only.
	Advanced users may prefer to add an alias in place of this function.
	The alias **should** override the entrypoint command set in rsudp's
	``setup.py``.

	On Linux and MacOS, adding an alias may look like this:

	.. code-block:: bash

		# add the alias definition to the aliases file
		echo "alias rsudp-settings='nano ~/.config/rsudp/rsudp_settings.json'" >> .bash_aliases
		# then reload the console
		bash

	To add an alias on Windows via the command prompt is much more difficult.

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
	.. versionadded:: 1.0.3

	This function uses a posix system's ``cat`` command to print messages in
	the rsudp log file. It is provided for convenience only.

	It is accessible via the console command ``rs-log`` on posix (Linux, MacOS)
	style operating systems.
	'''
	if os.name == 'posix':
		subprocess.call(('cat', log_loc))
	else:
		print('This command is only available on posix (Linux, MacOS) machines.')

def ep_tailf_log():
	'''
	.. versionadded:: 1.0.3

	This function uses a the system's follow command to follow new
	messages added to the log file. It is provided for convenience only.
	is the equivalent of ``tail -f /tmp/rsudp/rsudp.log`` on Linux/MacOS
	and ``Get-Content -Path "C:/tmp/rsudp/rsudp.log" -Wait`` on Windows.

	It is accessible via the console command ``rs-tailf``.

	The function will run until it receives a keyboard interrupt (CTRL+C).
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
			subprocess.call(('Get-Content', '-Path', '"C:/tmp/rsudp/rsudp.log"', '-Wait'))
		except Exception as e:
			print('This function is not available on Windows. Error: %s' % (e))
