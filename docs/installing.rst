Installing rsudp
#####################################

.. role:: bash(code)
   :language: bash

Installation is covered in `our installation tutorial video <https://youtu.be/e-kyg55GZyA>`_.


On Linux & MacOS
*********************************

A UNIX installer script is available at `unix-install-rsudp.sh`. This script checks whether or not you have Anaconda installed, then downloads and installs it if need be. This script has been tested on both `x86_64` and `armv7l` architectures (meaning that it can run on your home computer or a Raspberry Pi) and will download the appropriate Anaconda distribution, set up a virtual Python environment, and leave you ready to run the program. To install using this method:

.. code-block:: bash

    bash unix-install-rsudp.sh

.. note:: The installer script will pause partway through to ask if you would like to make the `conda` command executable by default. This is done by appending the line below to your `~/.bashrc` file.** This is generally harmless, but if you have a specific objection to it, hitting any key other than "y" will cause the script to skip this step. You will have to manually run the `conda` executable in this case, however. If you choose to do it manually later, the line appended to the end of `~/.bashrc` is the following (architecture-dependent):

    On x86 systems:

    .. code-block:: bash

        . $HOME/miniconda3/etc/profile.d/conda.sh

    or on ARMv7 architecture with Raspbian OS:

    .. code-block:: bash

        . $HOME/berryconda3/etc/profile.d/conda.sh

    where `$HOME` is the home directory of the current user.

.. note:: You can run `uname -m` to check your computer's architecture.*


On Windows
*********************************





`Back to top ↑ <#top>`_
