#!/bin/bash

dir_name="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )" # current directory
arch=$(uname -m)    # machine hardware 
conda="conda"       # anaconda executable or alias
if [[ "$arch" == "aarch64" ]]; then release='miniforge3'; elif [[ "$arch" == "armv"* ]]; then release='berryconda3'; else release='miniconda3'; fi
# conda install location:
prefix="$HOME/$release"         # $HOME/miniconda3 is default location
full="$HOME/anaconda3"          # full release install location
miniforge3="$HOME/miniforge3"   # MiniForge3
berryconda="$HOME/berryconda3"  # berryconda install location
miniconda="$HOME/miniconda3"    # miniconda install location
config="$HOME/.config/rsudp"    # config location
settings="$config/rsudp_settings.json"  # settings file

echo "Looking for existing installation..."

# first we have to test if there is an existing anaconda installation
# the simplest case, that the conda command works:
command -v conda >/dev/null 2>&1 &&
conda activate >/dev/null 2>&1 &&
conda_exists=1

if [ -z ${conda_exists+x} ]; then
  # if conda command doesn't exist,
  # Create symbolic link on MacOS if anaconda in opt directory
  if [[ "$os" == "Darwin" ]]; then
    if [ -f "/opt/miniconda3/bin/conda" ]; then
      ln -s /opt/miniconda3 "$miniconda"
    elif [ -f "/opt/anaconda3/bin/conda" ]; then
      ln -s /opt/anaconda3 "$full"
    fi
  fi
  if [ -f "$miniconda/bin/conda" ]; then
    # now we look in the default install location
    . $prefix/etc/profile.d/conda.sh &&
    conda activate &&
    conda_exists=1
  elif [ -f "$miniforge3/bin/conda" ]; then
    # look for a miniforge3 release
    . $miniforge3/etc/profile.d/conda.sh &&
    prefix=$miniforge3
    conda activate &&
    conda_exists=1
  elif [ -f "$berryconda/bin/conda" ]; then
    # look for a berryconda release
    . $berryconda/etc/profile.d/conda.sh &&
    prefix=$berryconda
    conda activate &&
    conda_exists=1
  elif [ -f "$full/bin/conda" ]; then
    # finally, look for a full release
    . $full/etc/profile.d/conda.sh &&
    prefix=$full &&
    conda activate &&
    conda_exists=1
  else
    conda="$prefix/bin/conda"
  fi
else
  prefix="$(cd $(dirname $(which conda))/../; pwd)"
fi

if [ ${conda_exists+x} ]; then
  echo "Found anaconda at $prefix"
  if [ -d $prefix/envs/rsudp ]; then
    rsudp_exists=1
    echo "rsudp environment exists at $prefix/envs/rsudp"
    read -rp $'Press Enter to continue with update, or type reinstall and press Enter to reinstall...\n' update_choice
    
    if [[ "$update_choice" == *"reinstall"* ]]; then
      echo "Removing existing rsudp"
      rm -rf $prefix/envs/rsudp
      echo "Reinstalling rsudp"
      /bin/bash $dir_name/bin/unix-install.sh
    else
      echo "Starting update script."
      /bin/bash $dir_name/bin/unix-update.sh
    fi
  else
    echo "No rsudp environment found."
  fi
fi

if [ -z ${rsudp_exists+x} ]; then
  echo "Starting install script."
  /bin/bash $dir_name/bin/unix-install.sh
fi
