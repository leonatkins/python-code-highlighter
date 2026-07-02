@echo off
rem Double-click this file in Windows Explorer to launch the highlighter GUI.
cd /d "%~dp0"

rem Prefer pythonw (no console window); fall back to the py launcher, then python.
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "highlighter.py"
    goto :eof
)

where py >nul 2>nul
if %errorlevel%==0 (
    start "" py -3 "highlighter.py"
    goto :eof
)

where python >nul 2>nul
if %errorlevel%==0 (
    start "" python "highlighter.py"
    goto :eof
)

echo Python was not found on your PATH.
echo Install Python 3 from https://www.python.org/downloads/ and be sure to
echo check "Add python.exe to PATH" during setup, then run this file again.
pause
