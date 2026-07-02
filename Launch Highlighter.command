#!/bin/bash
# Double-click this file in Finder to launch the highlighter GUI.
cd "$(dirname "$0")"

# Some Python installs (notably Homebrew's) ship WITHOUT tkinter, which this app
# needs. So don't just run "python3" — find the first interpreter that actually
# has tkinter (Tk) and use that.
has_tk() { "$1" -c 'import tkinter' >/dev/null 2>&1; }

CANDIDATES=(
    python3.13 python3.12 python3.11 python3.10
    /usr/bin/python3
    /opt/homebrew/bin/python3.13 /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11
    /usr/local/bin/python3.13 /usr/local/bin/python3.12 /usr/local/bin/python3.11
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3
    /Library/Frameworks/Python.framework/Versions/3.11/bin/python3
    python3
)

for py in "${CANDIDATES[@]}"; do
    if command -v "$py" >/dev/null 2>&1 && has_tk "$py"; then
        exec "$py" highlighter.py
    fi
done

# Nothing usable found — explain how to fix it and keep the window open.
echo "Could not find a Python 3 with tkinter (Tk) support."
echo
echo "Your default 'python3' is probably Homebrew's, which omits tkinter."
echo "Fix it with either of:"
echo "  • brew install python-tk          # adds Tk to your Homebrew Python"
echo "  • install from https://www.python.org/downloads/ (Tk is included)"
echo
echo "Then double-click this file again."
read -n 1 -s -r -p "Press any key to close..."
echo
