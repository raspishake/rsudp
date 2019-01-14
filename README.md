# rsh-UDP
### Tools for receiving and interacting with Raspberry Shake UDP data
*Written by @ivor and @iannesbitt*  
*This file is easiest to read at https://gitlab.com/osop-raspberry-shake/rsh-UDP/blob/master/README.md*

### the files in this repo:

1) [`raspberryShake.py`](#raspberryshakepy)
   - library of shake-related functions, to be used in a parent python program wanting to process data off a UDP port

2) [`rs2obspy.py`](#rs2obspypy)
   - example library that uses raspberryShake.py to process UDP data to obspy stream object with channel-specific traces. can be iterated.

3) `shake-UDP-packetLoss.py`
   - program that will report UDP data packet loss between a shake and a receiving computer 
    to be run on receiving computer

4) `shake-UDP-local.py`
   - program to read data off UDP port, to be run on shake computer directly

5) `shake-UDP-remote.py`
   - program to read data off UDP port, to be run on a computer not the shake

6) `obspy_example.py`
   - program to read UDP data to an ObsPy stream continuously, then plot it when the user presses CTRL+C

7) `live_example.py`
   - reads UDP data and continuously updates a plot, can be used from the command line. run `python live_example.py -h or --help` for details.


## How to use these tools

Before you do anything, you should read the [manual page on UDP](https://manual.raspberryshake.org/udp.html#udp). This will tell you how to forward UDP data from your shake to a port on your local computer. That page is available at https://manual.raspberryshake.org/udp.html#udp.

The standard way to utilize the Raspberry Shake's UDP capability is by forwarding the UDP stream to a computer on the same local network. If the Shake and the computer you're working on aren't on the same network, usually you have to aim the UDP stream at the router on your side, then fiddle with the port forwarding settings on your router to forward the data to a port at your device's IP address.

Here's a visual diagram demonstrating a local connection. Home routers typically don't block any internal traffic, so while the router is implied here, it doesn't need to be configured in any way, so it's left out of the diagram.
```
  __________                        Some port (eg. 8888) on
 / RS  Box /                            your computer
/_________/|----local-network---.      (192.168.1.104)
|        | /                    |     ._________________.
|________|/                     |     |.---------------.|
                                |     ||               ||
                                |     ||   -._ .-._    ||
                                |     ||               ||
                                |     ||   UDP DATA    ||
                                |     ||               ||
                                |     ||_______________||
                                |     /.-.-.-.-.-.-.-.-.\
                                '-->>/.-.-.-.-.-.-.-.-.-.\
                                    /.-.-.-.-.-.-.-.-.-.-.\
                                   /______/__________\___o_\
                                   \_______________________/
```

And here's one demonstrating a truly remote connection. In this case UDP data is being sent from a distant network to a port (10002) on the externally-facing part of your local router, and your router is forwarding that to port 8888 your computer. This can be done with any modern router, but unfortunately since there are so many routers out there, you'll have to figure out how to do this with your specific make and model yourself.

```
  __________                                                 Some port (eg. 8888) on
 / RS  Box /                                                      your computer
/_________/|---remote-network---.                                (192.168.1.104)
|        | /                    |                              ._________________.
|________|/              \      |     /  Port 10002 on         |.---------------.|
                          \_____|____/    your router          ||               ||
                          |__________|  (65.61.121.222)        ||   -._ .-._    ||
                                |                              ||               ||
                                |_______________               ||   UDP DATA    ||
                                  forwarding to \              ||               ||
                                  your computer  \             ||_______________||
                                   locally        \            /.-.-.-.-.-.-.-.-.\
                                                   `------->>>/.-.-.-.-.-.-.-.-.-.\
                                                             /.-.-.-.-.-.-.-.-.-.-.\
                                                            /______/__________\___o_\
                                                            \_______________________/
```


## raspberryShake.py
This is the heart of the library. Use this to open a port, get data packets, and interpret those packets to readable, but still pretty basic form.

#### Initializing a connection on a port

Basic usage must start with initializing the library with the `initRSlib()` and `openSOCK()` functions. *Keep in mind that once you open a port, you will not be able to open the same port elsewhere until you quit the program using the port.*

```
>>> import raspberryShake as rs
>>> rs.initRSlib(dport=8888, rssta='R0E05')
>>> rs.openSOCK()
2019-01-14 15:23:29 Opening socket on (HOST:PORT) localhost:8888
>>>
```

Then, you can read data packets off of the port and interpret their contents.

```
>>> packet = rs.getDATA()
>>> packet
"{'EHZ', 1547497409.05, 610, 614, 620, 624, 605, 646, 648, 693, 639, 669, 654, 645, 690, 656, 687, 667, 703, 650, 641, 634, 637, 706, 641, 671, 617}"
>>> rs.getCHN(packet)
'EHZ'
>>> rs.getTIME(packet)          # seconds since 1/1/1970 UTC; more on this below
1547497409.05
>>>
```

Time is represented in what's called a UNIX timestamp. This is the number of seconds since 00:00:00 on January 1, 1970, in UTC. Seismic libraries like [ObsPy](https://www.obspy.org/) will be able to interpret this number to date and time without you doing anything to modify it. Python's datetime library lets you do something similar.

```
>>> from datetime import datetime
>>> timestamp = rs.getTIME(packet)
>>> dt = datetime.utcfromtimestamp(timestamp)
>>> dt
datetime.datetime(2019, 1, 14, 20, 23, 29, 50000)
>>> print(dt)
2019-01-14 20:23:29.050000
>>>
```

Now let's look at the data stream and some of its attributes.

```
>>> rs.getSTREAM(packet)
[610, 614, 620, 624, 605, 646, 648, 693, 639, 669, 654, 645, 690, 656, 687, 667, 703, 650, 641, 634, 637, 706, 641, 671, 617]
>>>
```

The data stream is a list object with values representing raw voltage counts from the geophone. They're measured at whatever millisecond frequency your device measures at. For older models, this means 50 Hz (one sample every 20 ms), and for newer ones that's 100 Hz (one sample every 10 ms). Luckily, we've written a way to tell the sampling frequency mathematically.

```
>>> tr = rs.getTR('EHZ')        # elapsed time between packet transmissions, in milliseconds
>>> tr
250
>>> rs.getSR(tr, packet)        # the sampling rate in hertz
100
>>>
```

*Note the difference in units: elapsed milliseconds vs hertz.*

So the first sample occurs at `1547497409.05` and each subsequent sample is 10 ms (1000 ms / 100 Hz) later. It turns out that this is all we need to convert this raw data stream to, say, an ObsPy data trace.

## rs2obspy.py

`rs2obspy` is a way to get more complex and useful functionality from UDP data, by interpreting your Shake's UDP data and translating it to ObsPy data stream format. This library uses the `raspberryShake` library to initialize a port, get data on that port, then construct obspy traces and append them to an [ObsPy](https://www.obspy.org/) stream object. As such this library requires `obspy`.

### Initialize the library with a port and a station name

The basic functionality of the `rs2obspy` library is pretty simple. You initialize the library in almost the same way as the `raspberryShake` library, but you supply a station name as well. Once you open a port, you will not be able to open the same port elsewhere until you exit the program. The following is an example with an RS3D.

```
>>> import rs2obspy as rso
>>> rso.init(port=8888, sta='R4989')
2019-01-14 17:29:31 Opening socket on (HOST:PORT) localhost:8888
2019-01-14 17:29:31 Got data with sampling rate 100 Hz (calculated from channel EHZ)
2019-01-14 17:29:32 Found 3 channel(s): EHE EHN EHZ 
2019-01-14 17:29:32 Fetching inventory for station AM.R4989 from Raspberry Shake FDSN.
2019-01-14 17:29:32 Inventory fetch successful.
>>>
```

### Initialize a stream

Now you'll call the `init_stream()` function, which will return an obspy stream object with one trace inside (it will have processed one data packet).

```
>>> s = rso.init_stream()
2019-01-14 17:32:02 Initializing Stream object.
2019-01-14 17:32:02 Attaching inventory response.
>>> s
<obspy.core.stream.Stream object at 0x7f4b03496dd0>
>>> print(s)
1 Trace(s) in Stream:
AM.R4989.00.EHE | 2019-01-14T22:29:31.750000Z - 2019-01-14T22:29:31.990000Z | 100.0 Hz, 25 samples
>>> 
```

From here, you'll just need to update the stream for every data packet you receive using `update_stream()`. You'll need to feed it an already-initialized stream to update, like the example below. This is easiest with a loop, in which case the function will wait for data and automatically update when it receives something.

```
>>> s = rso.update_stream(s)
>>> s = rso.update_stream(s)
>>> print(s)
3 Trace(s) in Stream:
AM.R4989.00.EHZ | 2019-01-14T22:29:32.000000Z - 2019-01-14T22:29:32.240000Z | 100.0 Hz, 25 samples
AM.R4989.00.EHE | 2019-01-14T22:29:31.750000Z - 2019-01-14T22:29:31.990000Z | 100.0 Hz, 25 samples
AM.R4989.00.EHN | 2019-01-14T22:29:31.750000Z - 2019-01-14T22:29:31.990000Z | 100.0 Hz, 25 samples
>>>
```

Continuing to update the stream `s` using the `update_stream(s)` call will keep adding traces (one per data packet) to the stream, then merging them based on the channel. So you'll end up with a continuous stream with as many traces as there are channels on your Shake. And you'll have the full functionality of `obspy` at your fingertips.


### TO DO

1) finish library / add any other base functions of interest
	- library has been updated to work with current use cases

2) convert pgm 2 to completely use raspberryShake library

3) add an example program using obsPy library
	- done and working

4) document library

5) document packetLoss program as example of how to use library

6) flesh out the -local and -remote program templates, to use new library, etc.
	- done
    