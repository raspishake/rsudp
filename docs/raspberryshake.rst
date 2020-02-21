:py:data:`rsudp.raspberryshake` (main library)
=====================================================

This is the main library powering rsudp.
It contains common functions to open a port listener,
get data packets, parse the information in those packets,
and help consumer modules 

This library must be initialized using the following procedure:

.. code-block:: python

    >>> import rsudp.raspberryshake as rs
    >>> rs.initRSlib(dport=8888, rsstn='R940D')


.. automodule:: rsudp.raspberryshake
    :members:

................

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

`Back to top ↑ <#top>`_
