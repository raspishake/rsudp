rsudp as a ``systemctl`` daemon
################################################

Setup instructions
=====================

If you need rsudp to restart every time your Debain/Ubuntu machine boots,
this tutorial will work well for you.
This includes both raspbian (Raspberry Pi) and Ubuntu-like systems.
If you have an OS other than Linux, you will need to look elsewhere for
documentation regarding the creation and activation of daemon programs.

First of all, clone rsudp to ``~/bin/rsudp``:

.. code-block:: bash

    mkdir -p ~/bin
    cd ~/bin
    git clone https://github.com/raspishake/rsudp

If you have not already done so, install rsudp using the provided
installer script.

.. code-block:: bash

    bash ~/bin/rsudp/unix-install-rsudp.sh

Next, enter the following commands in order to set up a user systemd
directory structure.

.. code-block:: bash

    mkdir -p ~/.config/systemd/user/default.target.wants

Now create a new service file

.. code-block:: bash

    nano /home/pi/.config/systemd/user/rsudp.service

and paste the following code in it::

    [Unit]
    Description=rsudp daemon
    Documentation=https://github.com/iannesbitt/rsudp_pr
    After=graphical.target

    [Service]
    ExecStartPre=/bin/sleep 1
    ExecStart=/bin/bash /home/pi/bin/rsudp_pr/unix-start-rsudp.sh
    ExecStop=kill $MAINPID
    ExecReload=kill $MAINPID; /bin/bash /home/pi/bin/rsudp_pr/unix-start-rsudp.sh
    Restart=always
    RestartSec=10s

    [Install]
    WantedBy=default.target

Next, execute the following lines:

.. code-block:: bash

    systemctl --user daemon-reload
    sudo loginctl enable-linger "$USER"
    systemctl --user start rsudp.service

rsudp should start within about 30 seconds.
You can monitor the program's output in real time by doing the following command:

.. code-block:: bash

    tail -n 30 -f /tmp/rsudp/rsudp.log

If it does start correctly, you can enable the daemon to run permanently with this command:

.. code-block:: bash

    systemctl --user enable rsudp.service

You can test its enablement by restarting the entire system:

.. code-block:: bash

    sudo reboot

Restarting the daemon
==================================

Finally, if you need to restart the rsudp daemon service
(this may be necessary if your Shake changes IP or the network connection
is interrupted, or if rsudp freezes for some reason): 

.. code-block:: bash

    systemctl --user restart rsudp.service


Troubleshooting the daemon
=================================

If rsudp fails to start, you can run ``tail -n 30 -f /tmp/rsudp/rsudp.log``
to see what the error might be, or ``systemctl --user status rsudp.service``
to check whether the service file is misconfigured somehow.

A running daemon will show its status with green text saying "active (running)",
whereas a failed start will show red or grey text that will say
something like "inactive (failed)" or "inactive (dead)"
and will have some diagnostic text with which you can troubleshoot.


`Back to top ↑ <#top>`_

