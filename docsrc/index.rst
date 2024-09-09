`rsudp` |version|
#####################################
.. image:: https://img.shields.io/github/stars/raspishake/rsudp?style=social
    :target: https://github.com/raspishake/rsudp

| |github|
| **Continuous sudden motion and visual monitoring of Raspberry Shake data**
| *by Ian M. Nesbitt and Richard I. Boaz*
|
| *Maintained by Raspberry Shake, S.A. for use by the citizen science and seismology-in-school s communities.*

.. |github| raw:: html

   <a href="https://github.com/raspishake/rsudp" target="_blank">https://github.com/raspishake/rsudp</a>

.. |raspberryshake| raw:: html

   <a href="https://raspberryshake.org" target="_blank">Raspberry Shake</a>

Welcome to rsudp's documentation.
This program was written to parse and process live UDP data streams from
|raspberryshake| personal seismographs and
Raspberry Boom pressure transducer instruments.
rsudp allows users the options to see their data in real time, create alert parameters,
and be notified in various ways when their instrument detects sudden motion.
It is written in Python and is therefore highly customizable.

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
    daemon
    troubleshooting
    testing

.. toctree::
    :caption: Video resources

    youtube

.. toctree::
    :numbered:
    :maxdepth: 2
    :caption: Developers' guide

    theory
    contributing


.. _modules:

Code documentation
========================

The modules available in rsudp are organized by type below.

------------

.. toctree::
    :maxdepth: 2
    :caption: Library

    init
    raspberryshake
    helpers
    entry_points

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
    c_rsam
    c_alertsound
    c_plot
    c_tweet
    c_telegram
    c_forward
    c_write
    c_custom

.. toctree::
    :maxdepth: 2
    :caption: Testing modules

    t_testdata
    c_testing
    test
    packetize



Function index
==================

Need to look something up?

* :ref:`genindex`
* :ref:`search`

.. * :ref:`modindex`

`Back to top ↑ <#top>`_
