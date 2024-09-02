if [%1]==[check] goto :check
if [%1]==[install] goto :install
if [%1]==[activate] goto :activate
if [%1]==[install_rsudp] goto :install_rsudp
goto :EOF


:check
:: Check if there is an existing anaconda installation.
:: Called by ../win-install-rsudp.bat, ../win-start-rsudp.bat, win-install.bat, win-update.bat.
:: Output:     
::   %2: miniconda or anaconda root directory.
if [%2]==[] echo Missing anaconda root directory output. & goto :EOF

setlocal

:: First look at $PATH environment variable.
for %%i in (conda.exe) do set conda_exe=%%~$PATH:i
if defined conda_exe (
  for %%i in ("%conda_exe%\..\..") do (endlocal & set "%2=%%~fi")
  goto :EOF
)

:: If not in $PATH, look at some common directories.
for %%a in (miniconda3 anaconda3) do (
  for %%d in ("%USERPROFILE%" "%ALLUSERSPROFILE%" "%ProgramFiles%" "%ProgramFiles(x86)%") do (    
    if exist %%d\%%a\Library\bin\conda.bat (
      endlocal & set "%2=%%d\%%a"
	  goto :EOF
    )
  )
)
goto :EOF


:install
:: Install miniconda.
:: Called by win-install.bat.
:: Output:
::   %2: miniconda root directory.
if [%2]==[] echo Missing miniconda root directory output. & goto :EOF

setlocal

set release=miniconda3
set prefix=%USERPROFILE%\%release%
  
echo Install location: %prefix%
echo Ready to download %release%
echo The download is about 50 MB.
pause
  
:: conda does not like $PYTHONPATH, and $PYTHONPATH is deprecated,
:: so we can get away with disabling it during installation.
:: because it is sourced, it will come back when the user opens a new shell
:: and conda will complain about it directly to the user.
if defined PYTHONPATH set PYTHONPATH=
  
:: Check Windows 32 bit or 64 bit
reg Query "HKLM\Hardware\Description\System\CentralProcessor\0" | find /i "x86" > NUL && set OS=32BIT || set OS=64BIT
  
:: Set correct download url
if %OS%==32BIT set url=https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86.exe
if %OS%==64BIT set url=https://repo.anaconda.com/miniconda/Miniconda3-py312_24.5.0-0-Windows-x86_64.exe
  
powershell -Command "Invoke-WebRequest %url% -OutFile tmp.exe"
  
echo Installing %release%...
start /wait "" tmp.exe /InstallationType=JustMe /s /AddToPath=1 /RegisterPython=1 /S /D=%prefix%
echo Cleaning up temporary files...
del tmp.exe
  
set conda_exe=%prefix%\Scripts\conda.exe
  
echo Updating base conda environment...
%conda_exe% update conda -y
endlocal & set %2=%prefix%
goto :EOF


:activate
:: Activate conda.
:: Called by win-install.bat, win-update.bat.
:: Input:
::   %2: anaconda root directory
:: Output:
::   %3: conda.bat file
if [%2]==[] echo Missing anaconda installation directory. & goto :EOF
if [%3]==[] echo Missing conda.bat output. & goto :EOF

setlocal

set conda=%2\Library\bin\conda.bat
call %conda% activate
endlocal & set %3=%conda%
goto :EOF


:install_rsudp
:: Activate rsudp environment and install rsudp.
:: Called by win-install.bat, win-update.bat.
:: Input: 
::   %2: anaconda root directory.
::   %3: rsudp output directory.
if [%2]==[] echo Missing conda.bat file. & goto :EOF
if [%3]==[] echo Missing rsudp output directory & goto :EOF

setlocal

set conda=%2\Library\bin\conda.bat
set outDir=%3
set config=%USERPROFILE%\.config\rsudp
set settings=%config%\rsudp_settings.json

:: Activate rsudp environment.
echo Activating rsudp environment...
call %conda% activate rsudp && echo Success: rsudp environment activated. & set success=1

:: Install rsudp.
if defined success (
  echo Installing PyQt5...
  pip install pyqt5
  echo Installing rsudp...
  pip install "%cd%" && echo rsudp has installed successfully! || set success=
)

if not defined success (
  echo ---------------------------------
  echo Something went wrong.
  echo Check the error output and try again.
  goto :EOF
)

:: Settings
if exist %settings% (
  echo Backing up old settings file...
  copy %settings% %settings%.old
)
echo Installing new settings file...

if not exist %config% (mkdir %config% || goto :install_rsudp_error)

:: Dump a default setting file, then replace @@DIR@@ with outDir.
rs-client -i
if not exist %settings% goto :install_rsudp_error

powershell -Command "(gc %settings%) -replace '@@DIR@@', '%outDir%' | Out-File -encoding ASCII %settings%"
for /f tokens^=4^ delims^=^" %%i in ('FINDSTR output_dir %settings%') do set outdirSetting=%%i
if not defined outdirSetting goto :install_rsudp_error
if not %outDir%==%outdirSetting% goto :install_rsudp_error

echo Success.
goto :EOF

:install_rsudp_error
echo Failed to create settings file. Either the script could not create a folder at %config%, or dumping the settings did not work.
echo If you would like, you can dump the settings to a file manually by running the command
echo rs-client -d rsudp_settings.json
goto :EOF