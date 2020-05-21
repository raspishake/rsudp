setlocal

set ver=v0.2

echo --------------------------------------------
echo Raspberry Shake UDP client updater %ver%
echo Ian Nesbitt, Raspberry Shake S.A., 2019
echo --------------------------------------------
pause

set settings=%USERPROFILE%\.config\rsudp\rsudp_settings.json
if not exist %settings% (
  echo Could not find a settings file at %settings%
  echo Please copy your settings file there and re-run this script.
  goto :EOF
)

for /f tokens^=4^ delims^=^" %%i in ('FINDSTR output_dir %settings%') do set outdir=%%i
if not defined outdir (
  echo Cannot find output_dir field in %settings%
  goto :EOF
)

echo Output directory is %outdir%
if not exist %outdir% (
  echo Could not find an output folder in this location.
  echo Please check that the output_dir field in %settings% is correct.
  goto :EOF
)

echo %outdir% exists
echo Looking for conda installation...
call bin\win-conda.bat check conda_dir
if not defined conda_dir (
  echo Cannot find conda installation. Please try running the installer script.
  goto :EOF
)

echo Activating conda...
call bin\win-conda.bat activate %conda_dir% conda

:: Theoretically this case should never happen but keeping it around just because.
if not exist %conda_dir%\envs\rsudp (
  echo No rsudp environment exists. Please use the installer script.
  echo Exiting now.
  goto :EOF
)

echo A rsudp conda environment exists at %conda_dir%\envs\rsudp

call bin\win-conda.bat install_rsudp %conda_dir% %outDir%
