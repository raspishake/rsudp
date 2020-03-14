:py:data:`rsudp.packetize` (track packets)
=====================================================

The ``packetize`` module is a utility that turns miniSEED data into text files
containing the Raspberry Shake UDP data format (see :ref:`producer-consumer`).
It can be run either from another python module using the
:py:func:`rsudp.packetize.packetize` function, or from the command line.

Python usage:

.. code-block:: python

    from rsudp.packetize import packetize
    packetize('test.mseed', 'output.txt')

Command line usage:

.. code-block:: bash

    conda activate rsudp
    python packetize.py -i test.mseed -o output.txt

.. note::

    Command line usage must be done from within an environment in which
    ``obspy`` is installed as a python3 package.

.. automodule:: rsudp.packetize
    :members:

................

* :ref:`genindex`
* :ref:`search`
.. * :ref:`modindex`

`Back to top ↑ <#top>`_
