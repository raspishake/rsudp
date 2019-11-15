#!/bin/bash

ver="v0.2"
dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )" # current directory
arch=$(uname -m)    # machine hardware 
os=$(uname -s)      # kernel name
node=$(uname -n)    # node name
gnu=$(uname -a | grep GNU)  # is this GNU?
conda="conda"       # anaconda executable or alias
if [[ "$arch" == "armv"* ]]; then release='berryconda3'; else release='miniconda3'; fi
# conda install location:
prefix="$HOME/$release"         # $HOME/miniconda3 is default location
full="$HOME/anaconda3"          # full release install location
berryconda="$HOME/berryconda3"  # berryconda install location
miniconda="$HOME/miniconda3"    # miniconda install location
config="$HOME/.config/rsudp"    # config location
settings="$config/rsudp_settings.json"  # settings file

echo "--------------------------------------------"
echo "Raspberry Shake UDP client updater $ver"
echo "Ian Nesbitt, Raspberry Shake S.A., 2019"
echo "--------------------------------------------"
echo "Please follow instructions in prompts."
read -rp $'Press Enter to continue...\n'

echo "This script will need to use or create a directory to store miniSEED data and screenshots."
echo "Common choices might be $HOME/rsudp or $HOME/opt/rsudp"
echo "Where would you like the rsudp output directory to be located? You can use an existing one if you would like."
echo "Press Enter when done (if no input is given, the script will use $HOME/rsudp):"
read -e -p "" outdir
# sanitize user input
# replace $HOME with home dir
outdir="${outdir/#\~/$HOME}"
outdir="${outdir/#\$HOME/$HOME}"
# first, strip underscores
outdir=${outdir//_/}
# next, replace spaces with underscores
outdir=${outdir// /_}
# now, clean out anything that's not alphanumeric or an underscore
outdir=${outdir//[^a-zA-Z0-9_/]/}
# finally, lowercase with TR
outdir=`echo -n $outdir | tr A-Z a-z`
if [ -z "$var" ]; then
  echo "No directory was provided, using $HOME/rsudp"
  outdir="$HOME/rsudp"
fi

if [ -d "$outdir" ]; then
  echo "Using existing directory $outdir"
else
  mkdir -p $outdir &&
  echo "Successfully created output folder $outdir" ||
  echo "Could not create output folder in this location." ||
  exit 2
fi

# first we have to test if there is an existing anaconda installation
# the simplest case, that the conda command works:
echo "Looking for conda installation..."
command -v conda >/dev/null 2>&1 &&
conda activate >/dev/null 2>&1 &&
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
    prefix=$full &&
    conda activate &&
    conda_exists=1
  else
    conda="$prefix/bin/conda"
  fi
else
  prefix="$(cd $(dirname $(which conda))/../; pwd)"
fi

if [ -z ${conda_exists+x} ]; then
  echo "Cannot find conda installation; please try running the installer script."
  exit 2
fi

sourceline=". $prefix/etc/profile.d/conda.sh"
if grep -Fxq "$sourceline" "$HOME/.bashrc"; then
  echo "Source line already exists in $HOME/.bashrc"
  sourced=1
fi
echo "Sourcing..."
$sourceline
echo "Activating conda..."
conda activate && conda_exists=1

if [ -d $prefix/envs/rsudp ]; then
  echo "A rsudp conda environment exists at $prefix/envs/rsudp" &&
  echo "Do you want to update it?"
  read -rp $'Press Enter to use it or Ctrl+C to quit:\n' reinstall
else
  echo "No rsudp environment exists. Please use the installer script."
  echo "Exiting now."
  exit 2
fi

if [ -d $prefix/envs/rsudp ]; then
  echo "Activating rsudp environment..." &&
  conda activate rsudp && echo "Success: rsudp environment activated." &&
  echo "Installing rsudp..." &&
  pip install $dir && success=1
else
  echo "ERROR: rsudp failed to install."
fi

if [ ! -z ${success+x} ]; then
  echo "rsudp has installed successfully!"
  if [ -f $settings ]; then
    echo "Backing up old settings file..."
    if [ ! -z ${gnu+x} ]; then
      cp --backup=t --force $settings $settings
    else
      cp $settings $settings".old"
    fi
  fi
  echo "Installing new settings file..."
  mkdir -p $config &&
  rs-client -i &&      # secret install mode
  sed -i 's/@@DIR@@/'"$(echo $outdir | sed 's_/_\\/_g')"'/g' $settings &&
  echo "Success." ||
  echo "Failed to create settings file. Either the script could not create a folder at $config, or dumping the settings did not work." ||
  echo "If you would like, you can dump the settings to a file manually by running the command" ||
  echo "rs-client -d rsudp_settings.json"

  if [ -z ${previous_conda+x} ]; then
    if [ -z ${sourced+x} ]; then
      echo 'You will need to tell your shell where to find conda by entering ". ~/'"$release"'/etc/profile.d/conda.sh"'
      then='then '
    fi
    echo 'You can'$then' enter the command "conda activate rsudp" to activate the rsudp conda environment'
  else
    if [ -z ${sourced+x} ]; then
      echo 'You need to re-source your shell before using conda. To do this, type "source ~/.bashrc" or just open a new terminal window.'
      then='then '
    fi
    echo 'You can'$then' enter the rsudp conda environment by typing "conda activate rsudp"'
  fi
  echo 'and then run rsudp by using the command "rs-client -h"'
  exit 0
else
  echo "---------------------------------"
  echo "Something went wrong."
  echo "Check the error output and try again."
  exit 2
fi
