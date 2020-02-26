.. _running:

Running rsudp
#################################################

.. role:: bash(code)
   :language: bash

Starting rsudp on Unix
*************************************************

Unix users may prefer the easy-to-use start script available in the git repository:

.. code-block:: bash

    bash unix-start-rsudp.sh


.. _running-manually:

Starting on Windows, or manually on Unix
*************************************************

.. |start_run_tutorial| raw:: html

   <a href="https://youtu.be/HA9k3CzmgLI" target="_blank">rsudp start/run tutorial video</a>

This start method is covered in our |start_run_tutorial|.

1. First, to activate the conda environment, type :bash:`conda activate rsudp`.
2. Next, configure a datacast stream (formerly known as a UDP stream)
to forward data to an open port on the computer where this program is running.
By default this port is :code:`8888`.
3. The UNIX installer will create a settings file in :bash:`$HOME/.config/rsudp/rsudp_settings.json`.
Change the settings in this file to control how the client operates.
.. note::
    Windows users will need to type :bash:`rs-client -d default` to dump the settings to a file
    the first time they run this program.
.. note::
    To dump the default settings to a different location of your choosing, type
    :bash:`rs-client -d /path/to/settings.json`.
.. note::
    As stated above, to rebuild and overwrite the default settings file in
    :bash:`$HOME/.config/rsudp/rsudp_settings.json`, type :bash:`rs-client -d default`
4. After modifying the settings file to your liking,
type :bash:`rs-client` to use the settings file at :bash:`$HOME/.config/rsudp/rsudp_settings.json`,
or :bash:`rs-client -s /path/to/settings.json` to run with a settings file other than the default one.

.. note::
    This library can only handle incoming data from one Shake per port.
    If for some reason more than one Shake is sending data to the port,
    the software will only process data coming from the IP of the first Shake it sees sending data.
    All data coming from any other Shake(s) will be ignored.

`Back to top ↑ <#top>`_
