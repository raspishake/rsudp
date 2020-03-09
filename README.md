![Raspberry Shake event logo](https://raw.githubusercontent.com/raspishake/rsudp/master/docs/_static/logo.png)
# rsudp
### Tools for receiving and interacting with Raspberry Shake UDP data
*Written by Ian Nesbitt (@iannesbitt) and Richard Boaz (@ivor)*

[![PyPI](https://img.shields.io/pypi/v/rsudp)](https://pypi.org/project/rsudp/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/rsudp)](https://pypi.org/project/rsudp/)
[![GitHub](https://img.shields.io/github/license/raspishake/rsudp)](https://github.com/raspishake/rsudp/blob/master/LICENSE)
[![Documentation Status](https://readthedocs.org/projects/rsudp/badge/?version=latest)](https://rsudp.readthedocs.io/en/latest/?badge=latest)

`rsudp` is a tool for receiving and interacting with data casts from [Raspberry Shake](https://raspberryshake.org) personal seismographs and Raspberry Boom pressure transducer instruments.

`rsudp` has [full documentation](https://rsudp.readthedocs.io/) at Read the Docs. We also have [tutorial instructions](https://rsudp.readthedocs.io/en/latest/index.html#tutorial) to install, set up, and run rsudp there. Additionally, our documentation features [YouTube walkthroughs](https://rsudp.readthedocs.io/en/latest/youtube.html), a brief [Developer's guide](https://rsudp.readthedocs.io/en/latest/theory.html), and [module documentation](https://rsudp.readthedocs.io/en/latest/index.html#code-documentation).

`rsudp` contains eight main features:
1. **Alarm** - an earthquake/sudden motion alert trigger, complete with a bandpass filter and stream deconvolution capabilities
2. **AlertSound** - a thread that plays a MP3 audio file in the event of an alarm
3. **Plot** - a live-plotting routine to display data as it arrives on the port, with an option to save plots some time after an alarm
4. **Tweeter** - a thread that broadcasts a Twitter message when the alarm module is triggered, and optionally can tweet saved plots from the plot module
5. **Telegrammer** - a thread similar to the Tweeter module that sends a [Telegram](https://telegram.org) message when an alarm is triggered, which can also broadcast saved images
6. **Writer** - a simple miniSEED writer
7. **Forward** - forward a data cast to another IP/port destination
8. **Custom** - run custom code when an `ALARM` message is received
9. **Print** - a debugging tool to output raw data to the command line

`rsudp` is written in Python but requires no coding knowledge to run. Simply follow the [instructions to install the software](https://rsudp.readthedocs.io/en/latest/installing.html), go to your Shake's web front end, configure a UDP datacast to your computer's local IP address, [start the software]() from the command line, and watch the data roll in.

![Raspberry Shake logo](https://raw.githubusercontent.com/raspishake/rsudp/master/docs/_static/4d-event.png)

(Above) a plot of an earthquake on the two vertical channels of a Raspberry Shake 4D (EHZ---the geophone channel, and ENZ---the accelerometer vertical channel).