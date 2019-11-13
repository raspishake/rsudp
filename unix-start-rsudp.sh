#!/bin/bash

arch=$(uname -m)    # machine hardware 

# settings file (change this to start with a different settings file)
settings="$HOME/.config/rsudp/rsudp_settings.json"

# other necessary stuff
if [[ "$arch" == "armv"* ]]; then release='berryconda3'; else release='miniconda3'; fi
# conda install location:
prefix="$HOME/$release"         # $HOME/miniconda3 is default location
full="$HOME/anaconda3"          # full release install location

if [ -f "$prefix/etc/profile.d/conda.sh" ]; then
  . $prefix/etc/profile.d/conda.sh
elif [ -f "$full/etc/profile.d/conda.sh" ]; then
  . $full/etc/profile.d/conda.sh
else
  echo "Could not find an anaconda installation. Have you used the installer script to install rsudp, or is anaconda in a nonstandard location?"
  exit 2
fi
conda activate rsudp
echo "Installing from the git directory..."
mkdir -p /tmp/rsudp
touch /tmp/rsudp/rsudp.log
pip install $( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd ) &>/tmp/rsudp/rsudp.log
echo "Done."
rs-client -s $settings 2>/tmp/rsudp/rsudp.log