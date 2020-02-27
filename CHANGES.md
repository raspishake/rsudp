# Changelog
## changes in 0.4.3
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
