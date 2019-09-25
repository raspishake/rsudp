#!/bin/bash
#### this script must be run with the `source` command

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd /tmp

if [ "armv" in $(uname -m) ]; then
  wget https://github.com/jjhelmus/berryconda/releases/download/v2.0.0/Berryconda3-2.0.0-Linux-armv7l.sh -O berryconda.sh
  chmod +x berryconda.sh
  ./berryconda.sh -b
  rm berryconda.sh
  $HOME/berryconda3/bin/conda update conda -y
  echo ". /home/pi/berryconda3/etc/profile.d/conda.sh" >> ~/.bashrc
  . /home/pi/berryconda3/etc/profile.d/conda.sh
  conda activate
  conda config --add channels conda-forge
  conda create -n rsudp python=3 numpy matplotlib future scipy lxml sqlalchemy -y
  conda activate rsudp
  pip install matplotlib==3.1.1
  pip install obspy

else
  if [ "Linux" in $(uname -o) ]; then
    wget https://repo.anaconda.com/archive/Anaconda3-2019.07-Linux-x86_64.sh -O anaconda.sh
    chmod +x anaconda.sh
    ./anaconda.sh -b
    rm anaconda.sh
    $HOME/anaconda3/bin/conda update conda -y
    echo ". /home/pi/anaconda3/etc/profile.d/conda.sh" >> ~/.bashrc
    . /home/pi/anaconda3/etc/profile.d/conda.sh
    conda activate
    conda config --add channels conda-forge
    conda create -n rsudp python=3 matplotlib=3.1.1 numpy future scipy lxml sqlalchemy obspy -y
    conda activate rsudp

  else
    echo "Script does not support this architecture."
    echo "Please install Anaconda by hand from the following link:"
    echo "https://www.anaconda.com/distribution/#download-section"
    exit 1

  fi

fi

pip install $DIR && success=1 || success=0

if [ $success -eq "1" ]; then
  echo "---------------------------------"
  echo "rsudp has installed successfully!"
  echo "You can enter this conda environment by typing `conda activate rsudp`"
  echo "and run rsudp by using the command `shake_tool -h`"
else
  echo "---------------------------------"
  echo "Something went wrong."
  echo "Check the error output and try again."
  exit 1
fi
