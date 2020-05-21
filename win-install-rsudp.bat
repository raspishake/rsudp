@echo off
setlocal

echo Looking for existing anaconda installation...
call bin\win-conda.bat check conda_dir

if not defined conda_dir goto :install

echo Found anaconda at %conda_dir%

if exist %conda_dir%\envs\rsudp (
  echo rsudp environment exists at %conda_dir%\envs\rsudp
  echo Starting update script.
  bin\win-update.bat
) else (
  echo No rsudp environment found.
  :install
  echo Starting install script.
  bin\win-install.bat
)