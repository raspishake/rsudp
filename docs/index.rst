`rsudp` |version|
#####################################
| **Python tools for receiving and interacting with Raspberry Shake UDP data**
| *by Ian M. Nesbitt and Richard I. Boaz*

Welcome to rsudp's documentation.
This program was written to parse and process live UDP data streams from Raspberry Shake personal seismographs.
rsudp allows users the options to see their data in real time, create alert parameters,
and be notified in various ways when their instrument detects sudden motion.

The demands of real-time seismic processing, as in many types of scientific operations,
require that calculations must be made quickly and
remain stable for weeks or months without user intervention.
rsudp aims to achieve both of these things,
while maintaining a codebase lean enough to run on Raspberry Pi
but intuitive enough that users can learn the theory of
real time continuous data processing and contribute code of their own.
The project's source repository is `here <https://github.com/raspishake/rsudp>`_.

| In order to get a feel for what rsudp can do, check out our YouTube tutorials below.
| If you prefer to read in-depth documentation, follow our :ref:`tutorial`.
| Or, if you know what you're looking for, find it in :ref:`modules`.

YouTube walkthroughs
========================

1. Installation

    .. raw:: html

        <iframe width="400" height="225" src="https://www.youtube-nocookie.com/embed/e-kyg55GZyA" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

2. Adjust settings and run

    .. raw:: html

        <iframe width="400" height="225" src="https://www.youtube-nocookie.com/embed/HA9k3CzmgLI" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

3. rsudp detects `an earthquake <https://www.emsc-csem.org/Earthquake/earthquake.php?id=806235>`_!

    .. raw:: html

        <iframe width="400" height="225" src="https://www.youtube-nocookie.com/embed/pT_PkKKxFeM" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

4. Set up YouTube streaming (coming soon)


.. _tutorial:

.. toctree::
    :numbered:
    :maxdepth: 2
    :caption: Tutorial guide

    about
    installing
    settings
    running
    theory
    troubleshooting
    contributing

.. _modules:

Modules
========================

The modules available in rsudp are organized by type below.

------------

.. toctree::
    :maxdepth: 2
    :caption: Library

    raspberryshake

.. toctree::
    :maxdepth: 2
    :caption: Client

    client
    packetloss

.. toctree::
    :maxdepth: 2
    :caption: Producer and Consumer

    p_producer
    c_consumer

.. toctree::
    :maxdepth: 2
    :caption: Sub-Consumer

    c_alert
    c_alertsound
    c_plot
    c_tweet
    c_telegram
    c_forward
    c_write


Function index
==================

Need to look something up?

* :ref:`genindex`
* :ref:`search`
.. * :ref:`modindex`

`Back to top ↑ <#top>`_
