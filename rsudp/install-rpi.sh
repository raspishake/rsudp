#!/bin/bash
#### this script must be run with the `source` command
cd ~
wget https://github.com/jjhelmus/berryconda/releases/download/v2.0.0/Berryconda3-2.0.0-Linux-armv7l.sh
chmod +x Berryconda3-2.0.0-Linux-armv7l.sh
./Berryconda3-2.0.0-Linux-armv7l.sh -b

$HOME/berryconda3/bin/conda update conda -y

echo ". /home/pi/berryconda3/etc/profile.d/conda.sh" >> ~/.bashrc
source ~/.bashrc
conda activate
conda config --add channels conda-forge
conda create -n rsudp python=3 numpy matplotlib future scipy lxml sqlalchemy -y
conda activate rsudp
pip install matplotlib==3.1.1
pip install obspy
pip install rsudp
