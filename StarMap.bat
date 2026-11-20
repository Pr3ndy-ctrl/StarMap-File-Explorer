@echo off
rem StarMap File Explorer for Windows. Double-click to start; close this window to stop.
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 starmap.py %*
  goto end
)
where python >nul 2>nul
if %errorlevel%==0 (
  python starmap.py %*
  goto end
)
echo.
echo   StarMap needs Python 3.9 or newer.
echo   Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH",
echo   then double-click StarMap.bat again.
echo.
:end
pause
