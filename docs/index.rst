`rsudp` |version|
#####################################
|**Python tools for receiving and interacting with Raspberry Shake UDP data**
|*by Ian M. Nesbitt and Richard I. Boaz*

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

In order to get a feel for what rsudp can do, check out our YouTube tutorials:

==============================  ==============================
  Video                                  Link
==============================  ==============================
1. Installation                  https://youtu.be/e-kyg55GZyA
2. Adjust settings and run       https://youtu.be/HA9k3CzmgLI
3. YouTube streaming tutorial    (coming soon)
==============================  ==============================

If you prefer to read in-depth documentation, follow our :ref:`tutorial`.
Or, if you know what you're looking for, find it in :ref:`modules`.

.. _tutorial:

.. toctree::
    :numbered:
    :maxdepth: 2
    :caption: Tutorial

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


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

`Back to top ↑ <#top>`_
