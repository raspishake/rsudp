#!/bin/bash

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )" # current directory
arch=$(uname -m)    # machine hardware 
os=$(uname -s)      # kernel name
node=$(uname -n)    # node name
tmp="/tmp"          # temporary directory for install file
exe="conda-install.sh" # install file name
tmp_exe="$tmp/$exe" # install file loc/name
conda="conda"       # anaconda executable or alias
macos_exe="Miniconda3-4.7.10-MacOSX-x86_64.sh"
linux_exe="Miniconda3-4.7.10-Linux-x86_64.sh"
arm_exe="Berryconda3-2.0.0-Linux-armv7l.sh"
x86_base_url="https://repo.anaconda.com/miniconda/"
arm_base_url="https://github.com/jjhelmus/berryconda/releases/download/v2.0.0/"
if [[ "$arch" == "armv"* ]]; then release='berryconda3'; else release='miniconda3'; fi
# conda install location:
prefix="$HOME/$release"         # $HOME/miniconda3 is default location
full="$HOME/anaconda3"          # full release install location
berryconda="$HOME/berryconda3"  # berryconda install location
miniconda="$HOME/miniconda3"    # miniconda install location

echo "---------------------------------------"
echo "Raspberry Shake UDP client installer"
echo "Ian Nesbitt, Raspberry Shake S.A., 2019"
echo "---------------------------------------"
echo "Please follow instructions in script."
echo "---------------------------------------"
read -n1 -rsp $'Press any key to continue...\n\n'

# first we have to test if there is an existing anaconda installation
# the simplest case, that the conda command works:
command -v conda >/dev/null 2>&1 &&
conda activate &&
conda_exists=1

if [ -z ${conda_exists+x} ]; then
  # if conda command doesn't exist,
  if [ -f "$miniconda/bin/conda" ]; then
    # now we look in the default install location
    . $prefix/etc/profile.d/conda.sh &&
    conda activate &&
    conda_exists=1
  elif [ -f "$berryconda/bin/conda" ]; then
    # look for a berryconda release
    . $berryconda/etc/profile.d/conda.sh &&
    conda activate &&
    conda_exists=1
  elif [ -f "$full/bin/conda" ]; then
    # finally, look for a full release
    . $full/etc/profile.d/conda.sh &&
    conda activate &&
    conda_exists=1
  else
    conda="$prefix/bin/conda"
  fi
fi

if [ -z ${conda_exists+x} ]; then
  echo "Cannot find conda installation; will try installing $release."
  # get ready to install anaconda or berryconda
  echo "Found $os environment on $arch."
  echo "Install location: $prefix"
  echo "Ready to download $release"
  echo "The download could be as large as 200 MB."
  read -n1 -rsp $'Press any key to continue or Ctrl+C to exit...\n\n'

  if [[ "$arch" == "armv"* ]]; then
    # installing on ARM architecture (RPi or similar)
    rpi="rpi"

    if [[ "$node" == "raspberryshake" ]]; then
      # warn the user about installing on a Shake
      echo '---------------------------------------------------------------'
      echo "WARNING: You are installing this on the Raspberry Shake itself."
      echo "Although this is possible, it is not tested or supported."
      echo "Raspberry Shake S.A. is not liable for strange Shake behavior"
      echo "if you choose to do this! Proceed at your own risk."
      read -n1 -rsp $'Press any key to continue or Ctrl+C to exit...\n'
    fi

    wget "$arm_base_url$arm_exe" -O "$tmp_exe" && dl=1

  else
    if [[ "$os" == "Linux" ]]; then
      conda_installer=$linux_exe

    elif [[ "$os" == "Darwin" ]]; then
      conda_installer=$macos_exe

    else
      echo "ERROR: Script does not support this OS."
      echo "Please install Anaconda 3 by hand from the following link:"
      echo "https://www.anaconda.com/distribution/#download-section"
      exit 1
    fi

    wget "$x86_base_url$conda_installer" -O "$tmp_exe" && dl=1
  fi

  if [ ! -z ${dl+x} ]; then
    chmod +x "$tmp_exe"
    echo "Installing $release..."
    cd "$tmp" && ./$exe -b -p $prefix
    echo "Cleaning up temporary files..."
    rm "$tmp_exe"
    echo "Updating base conda environment..."
    $conda update conda -y
  else
    echo "Something went wrong downloading $release. Check the error and try again."
    exit 2
  fi

  if [ -f $prefix/etc/profile.d/conda.sh ]; then
    echo "----------------------------------------------"
    echo "The script will now append a sourcing line to your ~/.bashrc file in order to"
    echo 'make activating conda easier in the future (just type "conda activate" into a terminal).'
    read -n1 -rsp $'Press the "y" key to proceed, or any other key to prevent this...\n' key
    echo $key

    if [[ "$key" == "y" ]] || [[ "$key" == "Y" ]]; then
      echo "Appending sourcing line to bashrc..."
      echo ". $prefix/etc/profile.d/conda.sh" >> ~/.bashrc
    else
      echo "Not appending sourcing line to bashrc."
      echo "You can add it later by adding the following line to the bottom of ~/.bashrc:"
      echo ". $prefix/etc/profile.d/conda.sh"
    fi
    echo "Sourcing..."
    . $prefix/etc/profile.d/conda.sh
    echo "Activating conda..."
    conda activate && conda_exists=1
  else
    echo "Something went wrong; cannot find a conda profile to source. Exiting."
    exit 2
  fi
else
    echo "Anaconda installation found at $(which conda)"
fi

if [ -z ${conda_exists+x} ]; then
  echo "ERROR: Anaconda install failed. Check the error output and try again."
  exit 2
fi

if [[ "$arch" == "armv"* ]]; then
  env_install="conda create -n rsudp python=3.7.4 numpy matplotlib future scipy lxml sqlalchemy -y"
else
  env_install="conda create -n rsudp python=3.7.4 matplotlib=3.1.1 numpy=1.16.4 future scipy lxml sqlalchemy obspy -y"
fi

# check for conda forge channel; if it's not there add it
if [ -f $HOME/.condarc ]; then
  echo "No $HOME/.condarc file exists. Creating..."
  echo $'channels:\n  -\n   defaults\n  -\n   rpi\n  -\n   conda-forge\n' > $HOME/.condarc
fi
cat $HOME/.condarc | grep "conda-forge" ||
(echo "Appending conda-forge to channels..." &&
conda config --append channels conda-forge)
if [ ! -z ${rpi+x} ]; then
  cat $HOME/.condarc | grep "rpi" ||
  (echo "Appending rpi to channels..." &&
  conda config --append channels rpi)
fi
echo "Creating and installing rsudp conda environment..." &&
$env_install
if [ -d $prefix/envs/rsudp ]; then
  echo "Activating rsudp environment..." &&
  conda activate rsudp && echo "Success: rsudp environment activated." &&
  echo "Installing rsudp..." &&
  pip install $dir && success=1
else
  echo "ERROR: rsudp failed to install."
fi

if [ ! -z ${success+x} ]; then
  echo "---------------------------------"
  echo "rsudp has installed successfully!"
  echo 'You can enter the rsudp conda environment by typing "conda activate rsudp"'
  echo 'and then run rsudp by using the command "rs-client -h"'
  echo 'You may need to tell your shell where to find conda by entering ". ~/'"$release"'/etc/profile.d/conda.sh"'
  exit 0
else
  echo "---------------------------------"
  echo "Something went wrong."
  echo "Check the error output and try again."
  exit 2
fi
