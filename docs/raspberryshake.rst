:py:data:`rsudp.raspberryshake` (main library)
=====================================================

.. note::
    If you are starting this program from a command line by using
    :bash:`rs-client` or a start script, the functions in this
    library will be executed by the :func:`rsudp.client` automatically.
    See :ref:`running` for details.

    If you are a developer looking for helper functions to create a new module,
    you have come to the right place.

This is the main library powering rsudp.
It contains common functions to open a port listener,
get data packets, parse the information in those packets,
and help consumer modules update their data streams.

Prior to working with data from the port,
this library must be initialized using :func:`rsudp.raspberryshake.initRSlib`:

.. code-block:: python

    >>> import rsudp.raspberryshake as rs
    >>> rs.initRSlib(dport=8888, rsstn='R940D')

.. note:: This request will time out if there is no data being sent to the port.

After initializing the library, the :func:`rsudp.raspberryshake.getDATA`
function and its derivatives are available for use.


.. automodule:: rsudp.raspberryshake
    :members:

................

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

`Back to top ↑ <#top>`_
