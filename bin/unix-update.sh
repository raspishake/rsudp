#!/bin/bash

ver="v0.3"
yr="2022"
dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )" # current directory
arch=$(uname -m)    # machine hardware 
os=$(uname -s)      # kernel name
node=$(uname -n)    # node name
bsd=$(uname -a | grep BSD || uname -a | grep Darwin)  # is this a BSD variant?
conda="conda"       # anaconda executable or alias
if [[ "$arch" == "armv"* ]]; then release='berryconda3'; else release='miniconda3'; fi
# conda install location:
prefix="$HOME/$release"         # $HOME/miniconda3 is default location
full="$HOME/anaconda3"          # full release install location
miniforge3="$HOME/miniforge3"   # MiniForge3
berryconda="$HOME/berryconda3"  # berryconda install location
miniconda="$HOME/miniconda3"    # miniconda install location
config="$HOME/.config/rsudp"    # config location
settings="$config/rsudp_settings.json"  # settings file

echo "--------------------------------------------"
echo "Raspberry Shake UDP client updater $ver"
echo "Ian Nesbitt, Raspberry Shake S.A., $yr"
echo "--------------------------------------------"
read -rp $'Press Enter to continue...\n'

if [ -f "$HOME/.config/rsudp/rsudp_settings.json" ]; then
  if [ -z ${bsd+x} ]; then
    # use BSD grep
    outdir=$(grep -oE '(?<="output_dir": ").*?[^\\](?=",)' $HOME/.config/rsudp/rsudp_settings.json)
  else
    # use GNU grep
    outdir=$(grep -oP '(?<="output_dir": ").*?[^\\](?=",)' $HOME/.config/rsudp/rsudp_settings.json)
  fi
  echo "Output directory is $outdir"
else
  echo "Could not find a settings file at $HOME/.config/rsudp/rsudp_settings.json"
  echo "Please copy your settings file there and re-run this script."
  exit 2
fi

if [ -d "$outdir" ]; then
  echo "$outdir exists"
else
  echo "Could not find an output folder in this location."
  echo "Please check that the output_dir field in $HOME/.config/rsudp/rsudp_settings.json is correct."
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
  elif [ -f "$miniforge3/bin/conda" ]; then
    # look for a miniforge3 release
    . $miniforge3/etc/profile.d/conda.sh &&
    prefix=$miniforge3
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
  echo "A rsudp conda environment exists at $prefix/envs/rsudp"
else
  # theoretically this case should never happen but keeping it around just because
  echo "No rsudp environment exists. Please use the installer script."
  echo "Exiting now."
  exit 2
fi

if [ -d $prefix/envs/rsudp ]; then
  echo "Activating rsudp environment..." &&
  conda activate rsudp && echo "Success: rsudp environment activated." &&
  echo "Updating pip..." && pip install -U pip &&
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
