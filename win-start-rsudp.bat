@echo off
setlocal

:: Settings file (change this to start with a different settings file)
set settings="%USERPROFILE%\.config\rsudp\rsudp_settings.json"

call bin\win-conda.bat check conda_dir
if not defined conda_dir echo Could not find an anaconda installation. Have you used the installer script to install rsudp, or is anaconda in a nonstandard location? & goto :EOF

call bin\win-conda.bat activate %conda_dir% conda
call %conda% activate rsudp

echo Installing from the git directory...
mkdir %temp%\rsudp
type nul > %temp%\rsudp\rsudp.log
call pip install "%cd%" > %temp%\rsudp\rsudp.log 2>&1
echo Done.
call rs-client -s %settings%