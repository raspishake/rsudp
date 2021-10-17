:py:data:`rsudp.test` (test helpers)
=====================================================

.. versionadded:: 0.4.3

The test module. Here are the currently available tests, descriptions,
and their initial state:

.. code-block:: python

    TEST = {
        # permissions
        'p_log_dir':            ['log directory               ', False],
        'p_log_std':            ['stdout logging              ', False],
        'p_log_file':           ['logging to file             ', False],
        'p_output_dirs':        ['output directory structure  ', False],
        'p_screenshot_dir':     ['screenshot directory        ', False],
        'p_data_dir':           ['data directory              ', False],

        # network
        'n_port':               ['port                        ', False],
        'n_internet':           ['internet                    ', False],
        'n_inventory':          ['inventory fetch             ', False],

        # core
        'c_data':               ['receiving data              ', False],
        'c_processing':         ['processing data             ', False],
        'c_ALARM':              ['ALARM message               ', False],
        'c_RESET':              ['RESET message               ', False],
        'c_IMGPATH':            ['IMGPATH message             ', False],
        'c_TERM':               ['TERM message                ', False],

        # dependencies
        'd_pydub':              ['pydub dependencies          ', False],
        'd_matplotlib':         ['matplotlib backend          ', False],

        # consumers
        'c_miniseed':           ['miniSEED data exists        ', False],
        'c_img':                ['screenshot exists           ', False],
        'c_alerton':            ['alert trigger on            ', False],
        'c_alertoff':           ['alert trigger off           ', False],
        'c_tweet':              ['Twitter text message        ', False],
        'c_tweetimg':           ['Twitter text message        ', False],
        'c_telegram':           ['Telegram text message       ', False],
        'c_telegramimg':        ['Telegram text message       ', False],
    }

.. note::

    If you wish to add your own consumer module, the easiest way to test
    its functionality is to follow the instructions in
    :ref:`add_testing`, then add the relevant test to this dictionary.
    Then, you would import the :py:data:`rsudp.test.TEST` variable
    and modify the test result (:py:data:`TEST['your_test'][1] = True`)
    if the test passed.

    If your module is set not to start by default, and you are using the
    default settings file for testing, you will need to set
    ``settings['your_module']['enabled'] = True`` in
    :py:func:`rsudp.test.make_test_settings` prior to running the tests.




.. automodule:: rsudp.test
    :members:

................

* :ref:`genindex`
* :ref:`search`

.. * :ref:`modindex`

`Back to top ↑ <#top>`_
