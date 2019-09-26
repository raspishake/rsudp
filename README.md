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

A UNIX installer script is available at `installer.sh`. This script checks whether or not you have Anaconda installed, then downloads and installs it if need be. This script has been tested on both `x86_64` and `armv7l` architectures (meaning that it can run on your home computer or a Raspberry Pi) and will download the appropriate Anaconda distribution, set up a virtual Python environment, and leave you ready to run the program. To install using this method:

```bash
$ bash installer.sh
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

**Note: the installer script will make the `conda` command executable by default, by appending the line below to your `~/.bashrc` file.** This is generally harmless, but if you have a specific objection to it, you can run the installer with the `-c` flag, which will run the script and install the environment without modifying your `~/.bashrc`. You will have to manually run the `conda` executable in this case, however. If you choose to do it manually later, the line appended to `~/.bashrc` is the following:

```bash
. $HOME/anaconda3/etc/profile.d/conda.sh
```
where `$HOME` is the home directory of the current user (generally `/home/$USER` with `$USER` being your username).

### On Windows

1. Download and install [Anaconda](https://www.anaconda.com/distribution/#windows).
2. Open an Anaconda Prompt.
3. Execute the following lines of code:

```bash
conda config --add channels conda-forge
conda create -n rsudp python=3 matplotlib=3.1.1 numpy future scipy lxml sqlalchemy obspy
conda activate rsudp
pip install rsudp
```
