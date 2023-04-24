![Raspberry Shake event logo](https://raw.githubusercontent.com/raspishake/rsudp/master/docs/_static/logo.png)
# rsudp
### Continuous sudden motion and visual monitoring of Raspberry Shake data
*Written by Ian Nesbitt (@iannesbitt), Richard Boaz, and Justin Long (@crockpotveggies)*

[![PyPI](https://img.shields.io/pypi/v/rsudp)](https://pypi.org/project/rsudp/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/rsudp)](https://pypi.org/project/rsudp/)
[![GitHub](https://img.shields.io/github/license/raspishake/rsudp)](https://github.com/raspishake/rsudp/blob/master/LICENSE)
[![Documentation](https://img.shields.io/badge/docs-passed-brightgreen)](https://raspishake.github.io/rsudp/)
[![Build Status](https://scrutinizer-ci.com/g/raspishake/rsudp/badges/build.png?b=master)](https://scrutinizer-ci.com/g/raspishake/rsudp/build-status/master)
[![Code Coverage](https://scrutinizer-ci.com/g/raspishake/rsudp/badges/coverage.png?b=master)](https://scrutinizer-ci.com/g/raspishake/rsudp/?branch=master)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/raspishake/rsudp/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/raspishake/rsudp/?branch=master)
[![DOI](https://joss.theoj.org/papers/10.21105/joss.02565/status.svg)](https://doi.org/10.21105/joss.02565)

`rsudp` is a tool for receiving and interacting with data casts from [Raspberry Shake](https://raspberryshake.org) personal seismographs and Raspberry Boom pressure transducer instruments.

`rsudp` has [full documentation here](https://raspishake.github.io/rsudp/). We also have [tutorial instructions](https://raspishake.github.io/rsudp/index.html#tutorial) to install, set up, and run `rsudp` there. Additionally, our documentation features [YouTube walkthroughs](https://raspishake.github.io/rsudp/youtube.html), [notes for contributors](https://raspishake.github.io/rsudp/contributing.html), a brief [Developer's guide](https://raspishake.github.io/rsudp/theory.html), and [module documentation](https://raspishake.github.io/rsudp/#code-documentation).

We now have [a paper](https://doi.org/10.21105/joss.02565) published in The Journal of Open Source Software! You can reference `rsudp` using the following citation:

> Nesbitt et al., (2021). rsudp: A Python package for real-time seismic monitoring with Raspberry Shake instruments. Journal of Open Source Software, 6(68), 2565, https://doi.org/10.21105/joss.02565


`rsudp` contains ten main features:
1. **Alert** - an earthquake/sudden motion alert trigger, complete with a bandpass filter and stream deconvolution capabilities
2. **AlertSound** - a thread that plays a MP3 audio file in the event of the alert module signalling an alarm state
3. **Plot** - a live-plotting routine to display data as it arrives on the port, with an option to save plots some time after an alarm
4. **Tweeter** - a thread that broadcasts a Twitter message when the alert module is triggered, and optionally can tweet saved plots from the plot module
5. **Telegrammer** - a thread similar to the Tweeter module that sends a [Telegram](https://telegram.org) message when an alarm is triggered, which can also broadcast saved images
6. **Writer** - a simple miniSEED writer
7. **Forward** - forward a data cast to one or several IP/port destinations
8. **RSAM** - computes RSAM (Real-time Seismic AMplitude) and either prints or forwards it to an IP/port destination
9. **Custom** - run custom code when an `ALARM` message is received
10. **Print** - a debugging tool to output raw data to the command line

`rsudp` is written in Python but requires no coding knowledge to run. Simply follow the [instructions to install the software](https://raspishake.github.io/rsudp/installing.html), go to your Shake's web front end, [configure a UDP datacast](https://manual.raspberryshake.org/udp.html#configuring-a-data-stream-the-easy-way) to your computer's local IP address, [start the software](https://raspishake.github.io/rsudp/running.html) from the command line, and watch the data roll in.

![Earthquake plot recorded on a Raspberry Shake 4D](https://raw.githubusercontent.com/raspishake/rsudp/master/docs/_static/4d-event.png)

(Above) a plot of an earthquake on the four channels of a Raspberry Shake 4D (EHZ---the geophone channel, and EHE, EHN, and ENZ---the accelerometer east, north, and vertical channels).


### DISCLAIMER

RSUDP source code and software is provided "as is". No guarantee of functionality, performance, or advertised intent is implicitly or explicitly provided.

This project is free-to-use and free-to-copy, located in the public domain, and is provided in the hope that it may be useful.

Raspberry Shake, S.A., may, from time to time, make updates to the code base, be these bug fixes or new features.  However, the company does not formally support this software / program, nor does it place itself under any obligation to respond to bug reports or new feature requests in any prescribed time frame.

Like all public projects, end-users are encouraged to provide their own bug fixes and new features as they desire: create a new branch, followed by a merge request, to have the code reviewed and folded into the main branch.

We hope you enjoy RSUDP, playing with it, and perhaps even diving into the code to see how it can be made better!

TEAM RS

-----

## Added by @jadurani

I'm running this program on my Mac Apple Silicon Chip (M2). The client and testers run the app on Windows. The changes I've first added are related to the build scripts for running the machine specifically on Mac.

## rs-test

For running `rs-test`, you may use the settings file in [rsudp/test/rsudp_settings.json](rsudp/test/rsudp_settings.json).

```sh
rs-test -s /absolute/path/to/your/rsudp_settings.json
```

### Troubleshooting and changes added (Apple Silicon Chip)

1. syntax error near unexpected token

This might be an issue on the the text formats, especially if none of your syntax seems wrong at all. Install dos2unix (see [link](https://formulae.brew.sh/formula/dos2unix))

```sh
brew install dos2unix
```

Then update the bash scripts that throw this error. E.g.

```sh
dos2unix unix-install-rsudp.sh
```

And rerun the script(s)

```sh
bash unix-install-rsudp.sh
```

2. Protocol not supported

```
Exception in thread Thread-1:
2023-04-24 07:27:27 TESTING [openSOCK] Opening socket on localhost:8888 (HOST:PORT)
Traceback (most recent call last):
  File "/path/to/miniconda3/envs/rsudp/lib/python3.11/threading.py", line 1038, in _bootstrap_inner
2023-04-24 07:27:27 TESTING [RS lib] Waiting for UDP data on port 8888...
    self.run()
  File "/path/to/miniconda3/envs/rsudp/lib/python3.11/site-packages/rsudp/t_testdata.py", line 112, in run
    self.sock = s.socket(s.AF_INET, socket_type)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/path/to/miniconda3/envs/rsudp/lib/python3.11/socket.py", line 232, in __init__
    _socket.socket.__init__(self, family, type, proto, fileno)
OSError: [Errno 43] Protocol not supported
```

Investigate the files containing the following line:

```python
socket_type = s.SOCK_DGRAM if os.name in 'nt' else s.SOCK_DGRAM | s.SO_REUSEADDR
```

Check the following files in particular:

- /rsudp/c_forward.py
- /rsudp/c_rsam.py
- /rsudp/t_testdata.py

I've updated these files to support Apple Silicon Chip machine. The changes may not be backwards-compatible or supported by other machines.

After updating the files, run:

```bash
pip install -e .
```

3. Unexpected type 'float' on self.fig.canvas.start_event_loop

```sh
2023-04-24 07:48:09 TESTING [Alert] Earthquake trigger warmup time of 30 seconds...
2023-04-24 07:48:11 TESTING Traceback (most recent call last):
  File "/path/to/rsudp/rsudp/client.py", line 579, in test
    run(settings, debug=True)
  File "/path/to/rsudp/rsudp/client.py", line 358, in run
    start()
  File "/path/to/rsudp/rsudp/client.py", line 122, in start
    PLOTTER.run()
  File "/path/to/rsudp/rsudp/c_plot.py", line 665, in run
    self.setup_plot()
  File "/path/to/rsudp/rsudp/c_plot.py", line 503, in setup_plot
    self.fig.canvas.start_event_loop(0.005)             # wait for canvas to update
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/path/to/miniconda3/envs/rsudp/lib/python3.11/site-packages/matplotlib/backends/backend_qt5.py", line 468, in start_event_loop
    timer = QtCore.QTimer.singleShot(timeout * 1000, event_loop.quit)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: arguments did not match any overloaded call:
  singleShot(int, PYQT_SLOT): argument 1 has unexpected type 'float'
  singleShot(int, Qt.TimerType, PYQT_SLOT): argument 1 has unexpected type 'float'

2023-04-24 07:48:11 TESTING [Main] Ending tests.
```

It's likely that this is an error enountered only on my machine. :/

I updated the event loop timeout to be still be backwards compatible.

4. For issues related to audio, run:

```sh
brew install ffmpeg
```
