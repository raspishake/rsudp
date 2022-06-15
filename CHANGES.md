# Changelog
## changes in 1.1.1
- attempted to fix broken requirements in install script
- fixed small typos in paper
- fixed coverage tests in scrutinizer CI
- reset license to GPLv3 and moved disclaimer to its own file

## changes in 1.1.0
- changing version tag to reflect peer review status, and creating Zenodo record

## changes in 1.0.3
- changed matplotlib pin to be `<3.2` rather than `==3.1.1` to address [#21](https://github.com/raspishake/rsudp/issues/21)
- modified logos
- fixed unicode output error (emoji caused error on Windows machines)
- added version printout to rs lib initialization sequence
- simplified dependency imports
- fixed an error with the packetization script that caused it to break on files where the first trace in a given stream was not the shortest
- adjusted default alert settings to be more in line with what testing says is optimal
- adding entrypoint convenence functions `rs-settings`, `rs-log`, and `rs-tailf` to make editing settings and monitoring log output easier
- minor changes to paper manuscript and bib file

## changes in 1.0.2
- corrected install script to fix [#14](https://github.com/raspishake/rsudp/issues/14)
- corrected social media URL destination [#15](https://github.com/raspishake/rsudp/issues/15)
- adding feature requested in [#9](https://github.com/raspishake/rsudp/issues/9) (additional text for twitter posts [documented here](https://raspishake.github.io/rsudp/settings.html#tweets-twitter-notification-module))
- edited language as requested in [#13](https://github.com/raspishake/rsudp/issues/13)
- added feature requested in [#17](https://github.com/raspishake/rsudp/issues/17) to control forwarding of `ALARM` and `RESET` messages as well as data
- added feature requested in [#18](https://github.com/raspishake/rsudp/issues/18) to forward messages to multiple destinations (this changes the syntax of the `"address"` and `"port"` fields of the `"forward"` settings section to lists)
- changed logging structure to be more downstream-friendly. downstream software can now initialize logging to `/tmp/rsudp/XYZ.log` by calling `rsudp.start_logging(logname='XYZ.log')`
- addressed ([#23](https://github.com/raspishake/rsudp/issues/23)) which prevented data from being written to the output directory
- added tests for alert, alertsound, consumer, custom, forward, plot, printraw, rsam, producer, packetize, Telegram, Twitter, and write modules as suggested [in review](https://github.com/openjournals/joss-reviews/issues/2565) ([#22](https://github.com/raspishake/rsudp/issues/22))
- added `.coveragerc` and code coverage basics

## changes in 1.0.1
- added `rsudp.c_rsam` Real-time Seismic Amplitude Measurement consumer
- modified install scripts for clarity
- added Windows batch scripts for installation, updates, and running, to match Unix ones

## changes in 1.0.0
- settings changed to deconvolve plot channels by default
- added the ability to post to multiple Telegram chats (by spinning up multiple independent threads)
- moved several functions to a new `helpers.py` module
- simplified several functions to make them more readable
- changed doc structure to github pages compatible

## changes in 0.4.3
- added ability to run tests with any data file containing at least one of `SHZ, E[H,N][E,N,Z], HDF` channels (even miniSEED, which gets converted to text first then read by the pre-producer)
- cut whitespace from the beginning of included MP3s
- added standardized queue message constructors to `rsudp.raspberryshake`
- removed warning filters
- fixed plot trace offset issue
- fixed a problem where UTC would appear after link in telegram and tweet messages
- fixed problem with precision in event `UTCDateTime` objects
- fixed unit capitalization in plot y-label
- added an exit code to the test function
- added a custom thread class (`rsudp.raspberryshake.ConsumerThread`) for consumers to inherit which contains all internal flags that the Producer needs to function
- added additional trove classifiers
- alarm time in plot, telegrams, and tweets now has 0.01 second precision
- alarm time now reports directly from `rsudp.c_alert.Alert` instead of Producer
- fixed a circular import issue which manifest on RPi
- added earth gravity fraction deconvolution option ("GRAV", which is basically "ACC"/9.81)
- added testing capabilities using `rs-test`
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
