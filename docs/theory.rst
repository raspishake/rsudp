Program architecture and flow
#################################################

rsudp is laid out in a way that is standard for many continuous monitoring
softwares, but which may be unfamiliar to some developers.

The program's organization relies on two hierarchies: thread hierarchy and
data hierarchy. This allows the program to distribute data and messages
between different modules efficiently while maintaining programmatic
integrity required by rsudp's dependencies (:py:mod:`matplotlib` objects,
for example, can only be owned by the master thread).

.. _flow_diagram:
.. figure::  _static/rsudp-flow.png
    :align:   center

    Data and (inset) thread hierarchies for rsudp.
    This figure shows a flow chart of data as it makes its way through
    rsudp's producer-consumer architecture,
    and eventually to the end-consumer processing the data.
    Thread hierarchies are shown in the inset chart.
    If you are looking to add a module to rsudp,
    it will be a worker class (red) and will receive data from
    the master consumer like the rest of the workers.


Thread layout
*************************************************

The program relies on the :py:mod:`threading` and :py:mod:`queue` modules
to spin up multiple threads which all receive and work with data
independently of one another.

First, the :py:mod:`rsudp.client` (the "main" or "parent" thread) gathers
and parses settings. The client then instantiates the relevant
:py:class:`threading.Thread` objects as and passes settings and queues to
them. Next, it starts each of these consumer threads as "child" threads,
then finally the producer, also as a child thread.

If the :py:class:`rsudp.c_plot.Plot` thread is enabled, the program will
start that last, since plotting must be run as a loop controlled by the
main thread (:py:mod:`rsudp.client`) which can only be done once it has
started all of its child threads.


.. _producer-consumer:

Producer-consumer message passing
*************************************************

Data is read off the port by the data producer
(:py:class:`rsudp.p_producer.Producer`) and passed directly to the
(:py:class:`rsudp.c_consumer.Consumer`) via a first-in first-out (FIFO)
queue object.

This master consumer then duplicates these messages and
passes them to each sub-consumer queue destination in a list. At the
other end of each of these queues is a sub-consumer module, denoted
with a :py:data:`c_` before its module name.

Sub-consumers read messages from their queues and process data in
their logic loops. Some build :py:class:`obspy.core.stream.Stream` with
the data passed to them, while some ignore the data and watch for
status messages.

Message types
=================================================

Currently, the message types are as follows.

========= ==========================================
 Message              Format example
========= ==========================================
 data      ``b"{'EHZ', 1582315130.292, 14168, 14927, 16112, 17537, 18052, 17477, 15418, 13716, 15604, 17825, 19637, 20985, 17325, 10439, 11510, 17678, 20027, 20207, 18481, 15916, 13836, 13073, 14462, 17628, 19388}"``
 ALARM     ``b'ALARM 2020-02-23T06:56:40.598944Z'``
 IMGPATH   ``b'IMGPATH 2020-02-23T06:59:19.211704Z /home/pi/rsudp/screenshots/R24FA-2020-02-23-065919.png'``
========= ==========================================

**ALARM** messages are sent by :py:class:`rsudp.p_producer.Producer`
when it sees the :py:data:`rsudp.c_consumer.Alert.alarm` flag set to
``True``. This can trigger all sorts of actions. For example, when the
:py:class:`rsudp.c_alertsound.AlertSound` module is enabled and sees
this message, it uses ffmpeg or libav to play a sound. The social media
classes :py:class:`rsudp.c_tweet.Tweeter` and
:py:class:`rsudp.c_telegram.Telegrammer` both use this message to
instantly broadcast to their respective platforms.

**IMGPATH** messages are placed on the master queue by the
:py:func:`rsudp.c_plot.Plot.savefig` function, if and when a screenshot
figure is saved to disk. This is currently only used by the social media
modules, :py:class:`rsudp.c_tweet.Tweeter` and
:py:class:`rsudp.c_telegram.Telegrammer` which then send the saved image
to their respective social media platforms' APIs for broadcast.

Adding your own consumer modules
*************************************************

Adding consumer modules is easy in theory, when you understand the
workings of rsudp's layout. Using the existing modules' code architecture
is likely useful and should be encouraged, so feel free to follow along
with what we have already laid out in the code base.

As with other issues, if you have an idea for a feature addition but have
questions about how to implement it, we encourage you to post to our
forums at https://community.raspberryshake.org.

Thanks for supporting open source!


`Back to top ↑ <#top>`_
