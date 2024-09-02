#!/bin/bash

ver="v0.3"
yr="2022"
dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )" # current directory
arch=$(uname -m)    # machine hardware 
os=$(uname -s)      # kernel name
node=$(uname -n)    # node name
gnu=$(uname -a | grep GNU)  # is this GNU?
tmp="/tmp"          # temporary directory for install file
exe="conda-install.sh" # install file name
tmp_exe="$tmp/$exe" # install file loc/name
conda="conda"       # anaconda executable or alias
mpl="<3.2"          # matplotlib version
macos_exe="Miniconda3-py312_24.7.1-0-MacOSX-x86_64.sh"
macos_arm_exe="Miniconda3-py312_24.7.1-0-MacOSX-arm64.sh"
linux_exe="Miniconda3-py312_24.5.0-0-Linux-x86_64.sh"
aarch64_exe="Miniforge3-Linux-aarch64.sh"
arm_exe="Berryconda3-2.0.0-Linux-armv7l.sh"
x86_base_url="https://repo.anaconda.com/miniconda/"
aarch64_base_url="https://github.com/conda-forge/miniforge/releases/latest/download/"
arm_base_url="https://github.com/jjhelmus/berryconda/releases/download/v2.0.0/"
if [[ "$arch" == "aarch64" ]]; then release='miniforge3'; elif [[ "$arch" == "armv"* ]]; then release='berryconda3'; else release='miniconda3'; fi
# conda install location:
prefix="$HOME/$release"         # $HOME/miniconda3 is default location
full="$HOME/anaconda3"          # full release install location
miniforge3="$HOME/miniforge3"   # MiniForge3
berryconda="$HOME/berryconda3"  # berryconda install location
miniconda="$HOME/miniconda3"    # miniconda install location
config="$HOME/.config/rsudp"    # config location
settings="$config/rsudp_settings.json"  # settings file

echo "--------------------------------------------"
echo "Raspberry Shake UDP client installer $ver"
echo "Ian Nesbitt, Raspberry Shake S.A., $yr"
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
  echo "Cannot find conda installation; will try installing $release."
  # get ready to install anaconda or berryconda
  echo "Found $os environment on $arch."
  echo "Install location: $prefix"
  echo "Ready to download $release"
  echo "The download could be as large as 200 MB."
  read -n1 -rp $'Press any key to continue or Ctrl+C to exit...\n\n'

  if [ ! -z ${PYTHONPATH+x} ]; then
    # conda does not like $PYTHONPATH, and $PYTHONPATH is deprecated,
    # so we can get away with disabling it during installation.
    # because it is sourced, it will come back when the user opens a new shell
    # and conda will complain about it directly to the user.
    unset $PYTHONPATH
  fi

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
      read -n1 -rp $'Press any key to continue or Ctrl+C to exit...\n'
    fi

    wget "$arm_base_url$arm_exe" -O "$tmp_exe" && dl=1

  else
    if [[ "$os" == "Linux" ]]; then
      if [[ "$arch" == "aarch64" ]]; then
        conda_installer=$aarch64_exe
        wget "$aarch64_base_url$conda_installer" -O "$tmp_exe" && dl=1
      else
        conda_installer=$linux_exe
        wget "$x86_base_url$conda_installer" -O "$tmp_exe" && dl=1
      fi

    elif [[ "$os" == "Darwin" ]]; then
      if [[ "$arch" == "arm"* ]]; then
        conda_installer=$macos_arm_exe
      else
        conda_installer=$macos_exe
      fi
      curl "$x86_base_url$conda_installer" -o "$tmp_exe" && dl=1

    else
      echo "ERROR: Script does not support this OS."
      echo "Please install Anaconda 3 by hand from the following link:"
      echo "https://www.anaconda.com/distribution/#download-section"
      exit 1
    fi

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

else
    previous_conda=1
    echo "Anaconda installation found at $prefix"
    echo "conda executable: $(which conda)"
fi

comment="# added by rsudp/conda installer"
sourceline=". $prefix/etc/profile.d/conda.sh"

if grep -Fxq "$sourceline" "$HOME/.bashrc"; then
  echo "Source line already exists in $HOME/.bashrc"
  sourced=1
else
  echo "----------------------------------------------"
  echo "The script will now append a sourcing line to your ~/.bashrc file in order to"
  echo 'make activating conda easier in the future (just type "conda activate" into a terminal).'
  echo "This line is: $sourceline"
  read -rp $'Press Enter to continue, or type no and press Enter to prevent this...\n' key

  if [[ "$key" == "no" ]]; then
    echo "Not appending sourcing line to bashrc."
    echo "You can add it later by adding the following line to the bottom of ~/.bashrc:"
    echo $sourceline
  else
    echo "Appending sourcing line to bashrc..."
    echo $comment >> $HOME/.bashrc
    echo $sourceline >> $HOME/.bashrc
    sourced=1
  fi
fi
echo "Sourcing..."
$sourceline
echo "Activating conda..."
conda activate && conda_exists=1

if [ -z ${conda_exists+x} ]; then
  echo "ERROR: Anaconda install failed. Check the error output and try again."
  exit 2
fi

if [[ "$arch" == "armv"* ]]; then
  env_install="conda create -n rsudp python=3.12 numpy future scipy lxml cffi sqlalchemy cryptography -y"
else
  env_install="conda create -n rsudp python=3.12 numpy=2.0.1 future scipy lxml sqlalchemy cryptography -y"
fi

# check for conda forge channel; if it's not there add it
if [ ! -f $HOME/.condarc ]; then
  echo "No $HOME/.condarc file exists. Creating..."
  echo $'channels:\n  -\n   defaults\n  -\n   rpi\n  -\n   conda-forge\n' > $HOME/.condarc
fi
if [[ "$arch" == "armv"* ]]; then
  cat $HOME/.condarc | grep "rpi" >/dev/null && echo "Found rpi channel in $HOME/.condarc" ||
  (echo "Appending rpi to conda channels..." &&
  conda config --append channels rpi)
fi
cat $HOME/.condarc | grep "conda-forge" >/dev/null && echo "Found conda-forge channel in $HOME/.condarc"  ||
(echo "Appending conda-forge to conda channels..." &&
conda config --append channels conda-forge)

if [ -d $prefix/envs/rsudp ]; then
  echo "Another rsudp conda environment already exists at $prefix/envs/rsudp" &&
  echo "Do you want to use it, or remove it and install a new one?"
  read -rp $'Press Enter to use it, or type yes and press Enter to reinstall:\n' reinstall
  
  if [[ "$reinstall" == "yes" ]]; then
    echo "Removing old environment..."
    rm -r $prefix/envs/rsudp
    echo "Reinstalling rsudp conda environment..." &&
    $env_install
  fi
else
  echo "Creating and installing rsudp conda environment..." &&
  $env_install
fi

if [ -d $prefix/envs/rsudp ]; then
  echo "Activating rsudp environment..." &&
  conda activate rsudp && echo "Success: rsudp environment activated." &&
  echo "Upgrading pip..." && pip install -U pip &&
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
  sed -i.bak 's/@@DIR@@/'"$(echo $outdir | sed 's_/_\\/_g')"'/g' "$settings" && rm "$settings.bak" &&   # this sed command should work on both GNU and BSD
  echo "Success." ||
  echo "Failed to create settings file. Either the script could not create a folder at $config, or dumping the settings did not work." ||
  echo "If you would like, you can dump the settings to a file manually by running the command" ||
  echo "rs-client -d rsudp_settings.json"


  if [ -z ${previous_conda+x} ]; then
    if [ -z ${sourced+x} ]; then
      echo 'You will need to tell your shell where to find conda by entering ". ~/'"$release"'/etc/profile.d/conda.sh"'
      then=' then'
    fi
    echo 'You can'$then' enter the command "conda activate rsudp" to activate the rsudp conda environment'
  else
    if [ -z ${sourced+x} ]; then
      echo 'You need to re-source your shell before using conda. To do this, type "source ~/.bashrc" or just open a new terminal window.'
      then=' then'
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
