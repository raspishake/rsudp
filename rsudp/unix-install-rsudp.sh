#!/bin/bash
#### this script must be run with the `source` command

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
arch=$(uname -m)
os=$(uname -s)
command -v conda >/dev/null 2>&1 && conda_exists=1
conda='conda'

if [ ! $conda_exists ]; then
  if [ ! -f $CONDA_EXE ]; then
    echo "Cannot find conda executable; will try installing..."
  else
    echo "Using previously-installed conda executable $CONDA_EXE"
    conda=$CONDA_EXE
    conda_exists=1
  fi
fi

if [ ! $conda_exists ]; then
  cd /tmp

  if [ "armv" in $arch ]; then
    wget https://github.com/jjhelmus/berryconda/releases/download/v2.0.0/Berryconda3-2.0.0-Linux-armv7l.sh -O anaconda.sh
    install="$conda create -n rsudp python=3 numpy matplotlib future scipy lxml sqlalchemy -y"
    postinstall="pip install matplotlib==3.1.1; pip install obspy"

  else
    if [ "Linux" in $os ]; then
      conda_installer="Anaconda3-2019.07-Linux-x86_64.sh"

    elif [ "Darwin" in $os ]; then
      conda_installer="Anaconda3-2019.07-MacOSX-x86_64.sh"

    else
      echo "Script does not support this OS."
      echo "Please install Anaconda 3 by hand from the following link:"
      echo "https://www.anaconda.com/distribution/#download-section"
      exit 1

    fi

    echo "Found $os environment, downloading conda installer $conda_installer from Continuum..."
    wget https://repo.anaconda.com/archive/$conda_installer -O anaconda.sh
    install="$conda create -n rsudp python=3 matplotlib=3.1.1 numpy future scipy lxml sqlalchemy obspy -y"

  fi

  chmod +x anaconda.sh
  echo "Installing Anaconda..."
  ./anaconda.sh -b
  rm anaconda.sh
  echo "Updating base conda environment..."
  $conda update conda -y
  if [ ! $pres_bashrc ]; then
    echo "Appending sourcing line to bashrc..."
    echo ". /home/pi/anaconda3/etc/profile.d/conda.sh" >> ~/.bashrc
  fi
  echo "Sourcing..."
  . /home/pi/anaconda3/etc/profile.d/conda.sh

fi

echo "Activating Anaconda..."
$conda activate
echo "Appending conda-forge to channels..."
$conda config --append channels conda-forge
echo "Creating and installing (rsudp) environment..."
$install
echo "Activating rsudp environment..."
$conda activate rsudp && echo "Success: rsudp environment activated."
if [ $postinstall ]; then
  echo "Doing post-install tasks for rsudp environment..."
  $postinstall
fi
echo "Installing rsudp..."
pip install rsudp && success=1 || success=0

if [ $success -eq "1" ]; then
  echo "---------------------------------"
  echo "rsudp has installed successfully!"
  echo "You can enter the rsudp conda environment by typing `conda activate rsudp`"
  echo "and then run rsudp by using the command `shake_tool -h`"
  exit 0
else
  echo "---------------------------------"
  echo "Something went wrong."
  echo "Check the error output and try again."
  exit 2
fi
