:py:data:`rsudp.test` (test helpers)
=====================================================

.. versionadded:: 0.4.3

The test module. Here are the currently available tests:

.. code-block:: python

    TEST = {
        # permissions
        'p_log_dir':			['log directory               ', False],
        'p_log_std':			['stdout logging              ', False],
        'p_log_file':			['logging to file             ', False],
        'p_output_dirs':		['output directory structure  ', False],
        'p_screenshot_dir':		['screenshot directory        ', False],
        'p_data_dir':			['data directory              ', False],
        # network
        'n_port':				['port                        ', False],
        'n_internet':			['internet                    ', False],
        'n_inventory':			['inventory fetch             ', False],
        # dependencies
        'd_pydub':				['pydub dependencies          ', False],
        'd_matplotlib':			['matplotlib backend          ', False],

        # core
        'c_data':				['receiving data              ', False],
        'c_processing':			['processing data             ', False],
        'c_ALARM':				['ALARM message               ', False],
        'c_RESET':				['RESET message               ', False],
        'c_IMGPATH':			['IMGPATH message             ', False],
        'c_TERM':				['TERM message                ', False],
    }


.. automodule:: rsudp.test
    :members:

................

* :ref:`genindex`
* :ref:`search`
.. * :ref:`modindex`

`Back to top ↑ <#top>`_
