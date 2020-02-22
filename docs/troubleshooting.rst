Troubleshooting
#################################################

In general, troubleshooting should be fairly straightforward.
Most output goes either to the command line or to ``/tmp/rsudp/rsudp.log``.
If you have a recurring issue, please see if the logs give any indication
as to what is going on, and check relevant sections below.

By far the most common problem you'll run into if you are a first-time user
is the inability to see data coming in. Once you have a good setup worked out,
you will typically be able to start and run this program without errors.

.. _remote:

Remote (rsudp) side
*************************************************

No data received
=================================================

If you are getting an ``IOError('No data received')``, most likely one of three
things is wrong:

#. Your Shake is not forwarding to the correct address and port — see :ref:`local`
#. rsudp is configured to listen on the wrong port
#. There is a firewall between your computer and the Shake — see :ref:`middle`

In an error like this, your rsudp output will display some helpful info just
above the error text. Scroll up to where you see something like this:

.. code-block:: bash

    2020-02-22 21:49:01 [Init] ERROR: No data received in 10 seconds; aborting.
    2020-02-22 21:49:01 [Init]        Check that the Shake is forwarding data to:
    2020-02-22 21:49:01 [Init]        IP address: 192.168.1.118    Port: 8888
    2020-02-22 21:49:01 [Init]        and that no firewall exists between the Shake and this computer.

Make note of the values after **IP address** and **Port**.

First, check to make sure the address and port have been configured on
the Shake side to cast data to the address ``192.168.1.118`` and port ``8888``
— see :ref:`local`.

If you are sending data to a different port than 8888, check the ``"port"``
value in your settings file (``~/.config/rsudp/rsudp_settings.json``) reflects
the port to which data is being sent.

Finally, if you are for example sending data from a location outside your home
network to somewhere inside your home network, your router may not be letting
data come through the port you specified, and you may need to specify rsudp to
send data to the router's public (externally facing) IP address.

Data stops flowing or is inconsistent
=================================================

This may be due to network problems. rsudp is designed to be able to ingest all
data sent to it by the Shake. However, since the Shake uses UDP, which is not a
guaranteed delivery protocol, some packets may be dropped.

There are several reasons why this might happen.

#. You are using WiFi and there is an unstable connection
#. The router nodes between the Shake and your computer may restart or be overloaded
#. The Shake may be a great distance from your computer (across the globe)
#. The Shake or your computer may have a slow connection

Typically, if the Shake is connected via Ethernet, and sending to a computer that
also uses Ethernet, you will experience on average zero dropped packets in a given
24 hour period. However, if you are sending data across an unstable connection,
you could experience 40% or more dropped packets.

To monitor packet loss over time, you can run our :py:mod:`rsudp.packetloss` script.
For example, to report dropped packets on port 8888 in periods of 1 hour at a time:

.. code-block:: bash

    conda activate rsudp
    rs-packetloss -p 8888 -f 3600

where ``-p 8888`` specifies port 8888 and ``-f 3600`` specifies 3600 seconds between
reports.

This will run indefinitely until the CTRL+C keys are pressed.


.. _local:

Shake (local) side
*************************************************

To set up or change Datacasting (also known as data forwarding or UDP forwarding)
navigate to your Shake's home page, then click on ``Settings > DATACAST``.

In the above example, you should configure your Shake to send data to:

================= ================
Label              Value
================= ================
Target Host IP     192.168.1.118
Target Port        8888
================= ================

Then press the blue plus button on the right side of the row.

.. _middle:

Middle (firewalls)
*************************************************

Home network
=================================================

Almost every home router in existence has a firewall between the outside of the
network it resides on and the "inside", i.e. the local in-home network it is
responsible for. (If you're working on a :ref:`school-net`, this works slightly
differently)

Most home routers also have a feature called "Port Forwarding" which will forward
data through the firewall from an external port to an internal port at a specific
IP address.

In rsudp's case: if we assume your Shake is somewhere else (i.e. not on your home
network) then it will be forwarding data to the external side of your router, and
you will need to tell your router to let that data through and where to send it.

First of all, you will need to know your router's IP address. There are many
online services that will do this. One of the safer ways to figure it out is just
`searching "what is my IP" on DuckDuckGo
<https://duckduckgo.com/?q=what+is+my+IP&t=canonical&ia=answer>`_
(DuckDuckGo will not store your information, while many other sites will).
Your IP should appear right under the search bar.

Let's say DuckDuckGo tells you that your IP address is ``28.14.122.178``.

Let's look at the following configuration:

============== ================ ======================
Device          IP               Public or Private IP
============== ================ ======================
Your Shake      130.112.21.12    Public
Your router     28.14.122.178    Public (external)
Your router     192.168.1.1      Private (internal)
Your computer   192.168.1.118    Private
============== ================ ======================

In this case, you must configure your Shake to forward UDP data to address
``28.14.122.178`` at, for example, port ``8888`` (i.e. port 8888 on the external side
of your router). Then, configure your router to forward data on external UDP port
``8888`` to internal address ``192.168.1.118`` and port ``8888``.

You should then be able to receive data on your computer.

.. note::

    Some internet service providers (ISPs) do not let you change your router's
    settings yourself. In this case, you will need to call them and ask them to
    configure port forwarding for external port ``8888`` to forward data to the same
    port at the internal IP address ``192.168.1.118``.

.. _school-net:

School or university network
=================================================

If you are on a school or university network, often security is much more strict.
In your home network, data is usually free to move around internally on the
network. On school networks, individual devices are usually not allowed to talk
much to each other. So even if your Shake is on the internal network, you may
still need to talk to the school's IT team in order to give your Shake permission
to send data to another computer on the network.

They may be able to help with configuration of the setup as well, although they
usually have difficult jobs, so don't be too hard on them!


Other issues
*************************************************

If you are having an issue other than the one described above, please post the
issue you are having to our forum at https://community.raspberryshake.org. We
would be glad to help you solve your issue there.

If it turns out that we cannot solve it without a bug fix in the code, please
`submit a new issue <https://github.com/raspishake/rsudp/issues/new>`_.
Be sure to describe the problem clearly, attach your logs
(:code:`/tmp/rsudp/rsudp.log`) and/or copy/paste command line output
in triple backticks \`\`\` like this \`\`\` to format it as code.

Our small team thanks you for your patience and cooperation!


`Back to top ↑ <#top>`_
