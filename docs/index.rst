`rsudp` |version|
#####################################
| **Python tools for receiving and interacting with Raspberry Shake UDP data**
| *by Ian M. Nesbitt and Richard I. Boaz*

Welcome to rsudp's documentation.
This program was written to parse and process live UDP data streams from Raspberry Shake personal seismographs.
rsudp allows users the options to see their data in real time, create alert parameters,
and be notified in various ways when their instrument detects sudden motion.

| In order to get a feel for what rsudp can do, check out our :ref:`youtube` page.
| If you prefer to read in-depth documentation, follow our written :ref:`tutorial`.
| Or, if you know what you're looking for, find it in :ref:`modules`.


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

.. toctree::
    :caption: Video resources

    youtube

.. _modules:


Code documentation
========================

The modules available in rsudp are organized by type below.

------------

.. toctree::
    :maxdepth: 2
    :caption: Library

    raspberryshake

.. toctree::
    :maxdepth: 2
    :caption: Clients

    client
    packetloss

.. toctree::
    :maxdepth: 2
    :caption: Producer and Consumer

    p_producer
    c_consumer

.. toctree::
    :maxdepth: 2
    :caption: Sub-Consumers

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
