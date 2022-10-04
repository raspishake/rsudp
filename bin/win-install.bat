@echo off
setlocal EnableDelayedExpansion

set ver=v0.2
set defaultOutDir=%USERPROFILE%\rsudp

echo --------------------------------------------
echo Raspberry Shake UDP client installer %ver%
echo Ian Nesbitt, Raspberry Shake S.A., 2019
echo --------------------------------------------
echo Please follow instructions in prompts.
pause

echo This script will need to use or create a directory to store miniSEED data and screenshots.
echo Common choices might be %defaultOutDir%
echo Where would you like the rsudp output directory to be located? You can use an existing one if you would like.

:user_input
set /p outdir=Press Enter when done (if no input is given, the script will use %defaultOutDir%):

:: Sanitize user input.
:: First, strim beginning spaces. Noted: if input contains special characters, the bat might exit with "The syntax of the command is incorrect."
if defined outdir for /f "tokens=* delims= " %%a in ("%outdir%") do set outdir=%%a

if defined outdir (
  :: Replace spaces with underscores
  set "outdir=%outdir: =_%"
  
  :: Replace %USERPROFILE%
  set outdir=!outdir:%%USERPROFILE%%=%USERPROFILE%!
)

:: If user just pressed Enter or Space, use default.
if not defined outdir echo No directory was provided, using %defaultOutDir% & set outdir=%defaultOutDir%

if exist %outdir% (
  echo Using existing directory %outdir%
) else (
  mkdir %outdir% && (echo Successfully created output folder %outdir%) || (echo Could not create output folder in this location. & goto :user_input)
)

:: Install conda if not yet. Then activate conda.
call bin\win-conda.bat check conda_dir
if defined conda_dir (
  echo Anaconda installation found at %conda_dir%
) else (
  echo Cannot find conda installation. Will try installing miniconda3.
  call bin\win-conda.bat install conda_dir
)
call bin\win-conda.bat activate %conda_dir% conda

:: Add conda forge channel. It will ignore if already added.
call %conda% config --append channels conda-forge

:: (Re)install rsudp environment.
if exist %conda_dir%\envs\rsudp (
  echo Another rsudp conda environment already exists at %conda_dir%\envs\rsudp
  choice /M "Do you want to reinstall"
  if !errorlevel! EQU 1 (
    echo Removing old environment...
	rd /s/q "%conda_dir%\envs\rsudp"
	echo Reinstalling rsudp conda environment...
	call %conda% create -n rsudp python=3 numpy=1.16.4 future scipy=1.4.1 lxml sqlalchemy obspy -y
  )
) else (
  echo Creating and installing rsudp conda environment...
  call %conda% create -n rsudp python=3 numpy=1.16.4 future scipy=1.4.1 lxml sqlalchemy obspy -y
)

if not exist %conda_dir%\envs\rsudp (
  echo ERROR: rsudp failed to install.
  echo ---------------------------------
  echo Something went wrong.
  echo Check the error output and try again.
  goto :EOF
)

call bin\win-conda.bat install_rsudp %conda_dir% %outDir%