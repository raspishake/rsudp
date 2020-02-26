Installing rsudp
#####################################

.. role:: bash(code)
   :language: bash

.. |installation_video| raw:: html

   <a href="https://youtu.be/e-kyg55GZyA" target="_blank">installation tutorial video</a>

Installation is covered in our |installation_video|.


On Linux & MacOS
*********************************

A UNIX installer script is available at :bash:`unix-install-rsudp.sh`.
This script checks whether or not you have Anaconda or Miniconda installed,
then downloads and installs it if need be.
This script has been tested on both :bash:`x86_64` and :bash:`armv7l`
architectures (meaning that it can run on your home computer or a Raspberry Pi)
and will download the appropriate Anaconda distribution, set up a virtual Python environment,
and leave you ready to run the program. To install using this method:

.. code-block:: bash

    bash unix-install-rsudp.sh

.. warning::
    In order for this installer to work correctly,
    your Anaconda/Miniconda base directory must be in your home folder,
    for example: :bash:`~/anaconda3` or :bash:`~/miniconda3`.
    If this is not the case, you could end up with a second conda installation overriding your first.

.. note::
    **The installer script will pause partway through to ask if you would like to make the**
    :bash:`conda` **command executable by default.**
    **This is done by appending the line below to your** :bash:`~/.bashrc` **file.**
    This is generally harmless, but if you have a specific objection to it,
    hitting any key other than "y" will cause the script to skip this step.
    You will have to manually run the :bash:`conda` executable in this case, however.
    If you choose to do it manually later,
    the line appended to the end of :bash:`~/.bashrc` is the following (architecture-dependent):

    On x86 systems:

    .. code-block:: bash

        . $HOME/miniconda3/etc/profile.d/conda.sh

    or on ARMv7 architecture with Raspbian OS:

    .. code-block:: bash

        . $HOME/berryconda3/etc/profile.d/conda.sh

    where :bash:`$HOME` is the home directory of the current user.

.. note::
    You can run :bash:`uname -m` to check your computer's architecture.

You are now ready to proceed to the next section, :ref:`settings`.

Updating
---------------------------------

Unix users can update the repository to the latest development version by running the following commands:

.. code-block:: bash

    cd /rsudp/location
    git pull
    bash unix-install-rsudp.sh

The update script will replace the previous default settings file
(:bash:`~/.config/rsudp/rsudp_settings.json`) with a new settings file.
If you use the default settings file, you will need to copy some old values over to the new file.
The reason for this is that the default settings file may change (i.e. add or modify sections of values)
and thus must be rewritten when updating. On Linux, backed up settings files will be named
:bash:`~/.config/rsudp/rsudp_settings.json.~x~`, where :bash:`x` is an integer.
On Mac, the backed up file will simply be named :bash:`~/.config/rsudp/rsudp_settings.json~`.
To back up the settings file yourself to a location that will not be overwritten,
you can do a command similar to the following:

.. code-block:: bash

    cp ~/.config/rsudp/rsudp_settings.json ~/.config/rsudp/rsudp_settings.json.bak


On Windows
*********************************

1. Download and install Anaconda or Miniconda.
2. Open an Anaconda Prompt.
3. Execute the following lines of code:

.. code-block:: bash

    conda config --append channels conda-forge
    conda create -n rsudp python=3 matplotlib=3.1.1 numpy=1.16.4 future scipy lxml sqlalchemy obspy
    conda activate rsudp
    pip install rsudp

.. |windows_tutorial| raw:: html

   <a href="https://windowsloop.com/install-ffmpeg-windows-10/" target="_blank">this tutorial</a>

If you wish to play sounds on Windows, please follow steps 1-8 in |windows_tutorial|
in order to install :code:`ffmpeg` and add it to your system's path variable.


You are now ready to proceed to the next section, :ref:`settings`.


`Back to top ↑ <#top>`_
