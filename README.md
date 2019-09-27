# rsudp
![Raspberry Shake logo](doc_imgs/raspbery-shake-logo-2x.png)

### Tools for receiving and interacting with Raspberry Shake UDP data
*Written by Ian Nesbitt (@iannesbitt) and Richard Boaz (@ivor) for @osop*  

`rsudp` is a tool for receiving and interacting with UDP data sent from a Raspberry Shake seismograph. It contains four main features:
1. Print - a debugging tool to output raw UDP output to the command line
2. Alarm - an earthquake/sudden motion alert configured to run some code in the event of a recursive STA/LTA alarm trigger, complete with bandpass filter capability
3. Writer - a miniSEED writer
4. Plot - a live-plotting routine to display data as it arrives on the port

`rsudp` is written in Python but requires no coding knowledge to run. Simply go to your Shake's web front end, point a UDP data stream at your computer's local IP address, and watch as the data rolls in.

## Notes about `rsudp`

**Note: The port you send data to must be open on the receiving end.** In Windows, this may mean clicking "allow" on a firewall popup. On most other machines, the port you send UDP data to (8888 or 18001 are common choices) must be open to UDP traffic.

Generally, if you are sending data inside a local network, there will not be any router firewall to pass data through. If you are sending data to another network, you will almost certainly have to forward data through a firewall in order to receive it. Raspberry Shake cannot help you figure out how to set up your router to do this. Contact your ISP or network administrator, or consult your router's manual for help setting up port forwarding.

**Note: this program has not been tested to run on the Raspberry Shake itself.** Raspberry Shake is not liable to provide support for any strange Shake behavior should you choose to do this.


## Installation

### On Linux & MacOS

A UNIX installer script is available at `unix-install-rsudp.sh`. This script checks whether or not you have Anaconda installed, then downloads and installs it if need be. This script has been tested on both `x86_64` and `armv7l` architectures (meaning that it can run on your home computer or a Raspberry Pi) and will download the appropriate Anaconda distribution, set up a virtual Python environment, and leave you ready to run the program. To install using this method:

```bash
$ bash unix-install-rsudp.sh
```

Once you've done this, your conda environment will be available by typing:
```bash
$ conda activate rsudp
```
Your prompt should now look like the following:
```bash
(rsudp) $
```
From here, you can begin using the program.

**Note: the installer script will pause partway through to ask if you would like to make the `conda` command executable by default. This is done by appending the line below to your `~/.bashrc` file.** This is generally harmless, but if you have a specific objection to it, hitting any key other than "y" will cause the script to skip this step. You will have to manually run the `conda` executable in this case, however. If you choose to do it manually later, the line appended to the end of `~/.bashrc` is the following (architecture-dependent):

On x86 systems:
```bash
. $HOME/miniconda3/etc/profile.d/conda.sh
```
or on ARMv7 architecture with Raspbian OS:
```bash
. $HOME/berryconda3/etc/profile.d/conda.sh
```
*Note: You can run `uname -m` to check your computer's architecture.*

where `$HOME` is the home directory of the current user (generally `/home/$USER` with `$USER` being your username).

### On Windows

1. Download and install [Anaconda](https://www.anaconda.com/distribution/#windows) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).
2. Open an Anaconda Prompt.
3. Execute the following lines of code:

```bash
conda config --append channels conda-forge
conda create -n rsudp python=3 matplotlib=3.1.1 numpy=1.16.4 future scipy lxml sqlalchemy obspy
conda activate rsudp
pip install rsudp
```
## Using this software

First, you will need a UDP stream pointed at an open port on the computer you plan to run this on. By default this port is 8888. To list the default settings used by the program, type `shake_client -d` to print the default settings. To dump these settings to a file for modification, type `shake_client -d > rsudp_settings.json`.

After modifying the settings file to your liking, type `shake_client -s rsudp_settings.json` to run.

**Note:** This library can only handle incoming data from one shake per port. If for some reason more than one Shake is sending data to the port, the software will only process data coming from the IP of the first Shake it sees sending data.

## Settings

By default, the settings are as follows:

```json
{
"settings": {
	"port": 8888,
	"station": "Z0000"},
"printdata": {
	"enabled": false},
"alert": {
	"enabled": true,
	"sta": 6,
	"lta": 30,
	"threshold": 1.6,
	"exec": "eqAlert",
	"highpass": 0,
	"lowpass": 50,
	"channel": "HZ",
	"win_override": false,
	"debug": false},
"write": {
	"enabled": false,
	"outdir": "/home/pi",
	"channels": "all"},
"plot": {
	"enabled": true,
	"duration": 30,
	"spectrogram": false,
	"fullscreen": false,
	"channels": ["HZ", "HDF"]}
}
```

- **`settings`** contains `"port"` and `"station"` defaults. Change these if you are receiving the data at a different port than 8888, or if you would like to set your station name.

- **`printdata`** controls the debug module, which simply prints the Shake data packets it receives to the command line. Change `"enabled"` to `true` to activate.

- **`write`** controls a very simple miniSEED writer. Every 10 seconds, seismic data is appended to a file with a descriptive name in the directory specified after `"outdir"`. By default, this directory is `"/home/pi"` which will need to be changed to the location of an existing directory on your machine or it will throw an error. By default, `"all"` channels will be written to their own files. You can change which channels are written by changing this to, for example, `["EHZ", "ENZ"]`, which will write the vertical geophone and accelerometer channels from RS4D output.

- **`plot`** controls the thread containing the plotting algorithm. This module can plot seismogram data from a list of 1-4 Shake channels, and optionally calculate and display a spectrogram alongside each (to do this, set `"spectrogram"` to `true`). By default the `"duration"` in seconds is `30`. The longer the duration, the more time it will take to plot, especially when the spectrogram is enabled. To put this plot into kiosk mode, set `"fullscreen"` to `true`. On a Raspberry Pi 3B+ plotting 600 seconds' worth of data and a spectrogram from one channel, the update frequency is approximately once every 5 seconds, but more powerful processors should be able to keep up with the data rate for larger-than-default `"duration"` values and more than just one channel.

- **`alert`** controls the alert module (please see [Disclaimer](#disclaimer) below). The alert module is a fast recursive STA/LTA sudden motion detector that utilizes obspy's [recursive_sta_lta()](https://docs.obspy.org/tutorial/code_snippets/trigger_tutorial.html#recursive-sta-lta) function. STA/LTA algorithms calculate a ratio of the short term average of station noise to the long term average. The data can be highpass, lowpass, or bandpass filtered by changing the `"highpass"` and `"lowpass"` parameters from their defaults (0 and 50 respectively). By default, the alert will be calculated on raw count data from the vertical geophone channel (either `"SHZ"` or `"EHZ"`). It will throw an error if there is no Z channel available (i.e. if you have a Raspberry Boom with no geophone). If you have a Boom and still would like to run this module, change the default channel `"HZ"` to `"HDF"`.

  If the STA/LTA ratio goes above a certain value, then the module runs a function passed to it. By default, this function is `rsudp.udp2obspy.eqAlert()` which just outputs some text. You can change the eqAlert function to do whatever you want or optionally, supply a path to executable Python code to run with the `exec()` function. Be very careful when using the `exec()` function, as it is known to have problems. Notably, it does not check the passed code for errors prior to running. If the code takes too long to execute, you could end up losing data packets, so keep it simple (sending a message or a tweet is really the intended purpose). In testing, we were able to get the pydub software to play 15 second-long sounds without losing any data packets. Theoretically you could run code that takes longer to process than that, but the issue is that the longer it takes the function to process code, the longer the module will go without processing data from the queue (the queue can hold up to 2048 packets, which for a RS4D works out to 128 seconds' worth of data).

  If you are running Windows and have code you want to pass to the `exec()` feature, Python requires that your newline characters are in the UNIX style (`\n`), not the standard Windows style (`\r\n`). To convert, follow the instructions in one of the answers to this [stackoverflow question](https://stackoverflow.com/questions/17579553/windows-command-to-convert-unix-line-endings). If you're not sure what this means, please read about newline/line ending characters [here](https://en.wikipedia.org/wiki/Newline). If you are certain that your code file has no Windows newlines, you can set `"win_override"` to `true`.

## Disclaimer

**NOTE: It is extremely important that you do not rely on this code to save life or property.** Raspberry Shake is not liable for errors running the Alert module or any other part of this library; it is meant for hobby and non-professional notification use only. If you need professional software meant to provide warning that saves life or property please contact Raspberry Shake directly or look elsewhere.

