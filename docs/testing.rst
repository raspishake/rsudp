Testing and demoing rsudp
#################################################

rsudp includes a small piece of software meant to test the
ability to function.
This could be useful if you are looking to demonstrate rsudp's
functionality to someone, perhaps a classroom of students,
or if you need to test the core functionality like alerts
and sounds.

The testing functions are useful for figuring out local problems.
That is, the testing capabilities of rsudp are meant to discover
whether or not the software can feed data to `itself` and
process it.

If you can run this testing program without any problems
but you are having issues getting the software to see data from
your own Raspberry Shake or boom, see the :ref:`troubleshooting`
page.


Using the testing functionality
=================================================

The testing modules of this software are designed to read a small
data file from disk and send its contents to the test port one
line at a time. The program functions essentially as it would if
it were receiving remote data, but instead it is feeding data
to itself.

This means that you can demo the software even if you don't have
a Raspberry Shake, or even use the testing functionality to check
whether or not an arbitrary piece of archival Raspberry Shake
data will trigger an alarm in the software.

To run this software, make sure you have installed this software
using the instructions in :ref:`install`, and that you can enter
your conda environment (typically by typing
``conda activate rsudp`` in a command window.

Once you have done that, the test command ``rs-test`` will become
available.

Type ``rs-test`` to watch earthquake detection in
action. The test will last about 120 seconds, over which time
various bits of functionality will be tested, including ports,
directory permissions, internet, processing routines,
alert functionality, sound-playing capability, and more.

It does test whether it can see the internet at large,
and whether it can send data to its own port
(we've chosen 18888 as a test port).
However, it does not test the ability to receive data from a
remote shake. If you are having trouble with that, please see the
:ref:`troubleshooting` page.


Settings during testing
=================================================

Settings are slightly different during testing than they would
ordinarily be. Find a summary of what gets changed at
:py:func:`rsudp.test.make_test_settings`.


.. _testing_flow:

Data flow during testing
=================================================

During testing, the typical data flow as depicted in
:ref:`flow` must be created artificially.
So, instead of getting data from the Raspberry Shake as usual,
the :py:class:`rsudp.t_testdata.TestData` thread reads a file and
sends the individual lines in that file to the data port.
The Producer then reads that data and data flow through the rest
of the architecture continues as normal.

.. _test_diagram:
.. figure::  _static/test-flow.png
    :align:   center

    Flow chart of test data hierarchy,
    based on the :ref:`flow` diagram, showing how data
    makes its way through the program during testing.
    Note that there is no Raspberry Shake in the hierarchy
    as there would be in ordinary operation, but instead
    data is generated from a text file at
    ``rsudp/test/testdata``.

Using your own data
=================================================

.. |canread| raw:: html

   <a href="https://docs.obspy.org/packages/autogen/obspy.core.stream.read.html#supported-formats" target="_blank">can read</a>


Included in this software is a small script that will convert
small seismic data files (basically anything that obspy |canread|)
to the UDP packet format required by rsudp.
This file is available at ``rsudp/test/packetize.py``
and can be run from the command line by doing

.. code-block:: bash

    conda activate rsudp
    python packetize.py -i input.mseed -o testdata

Then, running ``rs-test`` will use your own data for testing
plots and alerts.

.. note::

    Currently, the rsudp testing module only reads the test file
    at ``rsudp/test/testdata``, so your output file from the
    ``packetize.py`` script must end up there. 


`Back to top ↑ <#top>`_
