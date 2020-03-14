# Changelog
## changes in 0.4.3
- cut whitespace from the beginning of included MP3s
- added standardized queue message constructors to `rsudp.raspberryshake`
- removed warning filters
- fixed plot trace offset issue (don't know where it stems from, however)
- fixed a problem where UTC would appear after link in telegram and tweet messages
- fixed problem with precision in event `UTCDateTime` objects
- fixed unit capitalization in plot y-label
- added an exit code to the test function
- added a custom class (`rsudp.raspberryshake.ConsumerThread`) for consumers to inherit which contains everything the Producer needs to function
- added additional trove classifiers
- alarm time in plot, telegrams, and tweets now has 0.1 second precision
- alarm time now reports directly from `rsudp.c_alert.Alert` instead of Producer
- fixed a circular import issue which manifest on RPi
- added earth gravity fraction deconvolution option ("GRAV", which is basically "ACC"/9.81)
- added a testing module
- added a script to translate seismic data to Raspberry Shake UDP packet format for testing
- changed warning and error message colors in terminal stdout
- alert module stdout STA/LTA messages now colorized
- added `rsudp.c_custom` as an independent thread to run custom code
- added and expanded explicit docstrings and comments, as well as Sphinx `conf.py` file
- turned off alert module STA/LTA live printed output when `settings['settings']['debug']` is `False` in order to keep systemd log file size down
- streamlined alert sound module operation; no longer writes temporary sound file on every alert when using `ffplay`
- added `rsudp.__version__` linked to version in `setup.py`

## changes in 0.4.2
- the station's [Flinn-Engdahl region](https://en.wikipedia.org/wiki/Flinn%E2%80%93Engdahl_regions) is added to tweets when the station inventory is available through FDSN
- changed message format to include live link to StationView
- added redundancy to tweets
- added Telegram bot module (https://core.telegram.org/bots)

## changes in 0.4.1
- fixed [#1](https://github.com/raspishake/rsudp/issues/1) which caused the writing module to crash on some machines
- added a module that posts to twitter in the event of an alert, and can also post screenshots saved by the plot module
- fixed [#2](https://github.com/raspishake/rsudp/issues/2) which caused an error at 28>1 30>1 and 31>1 month rollovers
    - should also address issues arising from leap second addition
- added Twitter bot module (https://developer.twitter.com/en/apps)
