@echo off
rem Double-click this file in Windows Explorer to launch the highlighter GUI.
cd /d "%~dp0"

rem Pick a console Python for checks and a windowed one (pythonw) to launch with.
set "PY="
set "PYW="
where python  >nul 2>nul && set "PY=python"
if not defined PY ( where py >nul 2>nul && set "PY=py -3" )
where pythonw >nul 2>nul && set "PYW=pythonw"
if not defined PYW set "PYW=%PY%"

if not defined PY (
    echo Python 3 was not found on your PATH.
    echo Install it from https://www.python.org/downloads/ and tick
    echo "Add python.exe to PATH" during setup, then run this file again.
    pause
    goto :eof
)

rem Make sure tkinter (Tk) is present before launching.
%PY% -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo Your Python is missing tkinter ^(Tk^).
    echo Re-run the python.org installer and enable "tcl/tk and IDLE",
    echo or reinstall Python from https://www.python.org/downloads/ which
    echo includes it by default. Then run this file again.
    pause
    goto :eof
)

start "" %PYW% "highlighter.py"
