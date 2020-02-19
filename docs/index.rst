`rsudp` |version| documentation
#####################################

Welcome to rsudp's documentation. This program was written to parse and process live UDP data streams from Raspberry Shake personal seismographs. rsudp allows users the options to see their data in real time, create alert parameters, and be notified in various ways when their instrument detects sudden motion.

The demands of real-time seismic processing, as in many types of scientific operations, require that calculations must be made quickly and that monitoring or educational kiosk applications require that a program remain active for weeks or months without user intervention. rsudp aims to achieve both of these things, while maintaining a codebase lean enough to run on Raspberry Pi but intuitive enough that users can learn the theory of real time continuous data processing and contribute code of their own.

The project's source repository is `here <https://github.com/raspishake/rsudp>`_.

.. toctree::
    :numbered:
    :maxdepth: 2
    :caption: Tutorial

    installing
    running
    detail
    troubleshooting
    contributing

.. toctree::
    :maxdepth: 2
    :caption: Modules

    client
    p_producer
    c_consumer
    c_alert
    c_alertsound
    c_plot
    c_tweet
    c_telegram
    c_forward
    c_write
    raspberryshake
    shake_udp_packetloss

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

`Back to top ↑ <#top>`_
