#!/bin/bash
# Double-click this file in Finder to launch the highlighter GUI.
cd "$(dirname "$0")"

# Pick a Python that has a *usable* tkinter. Two gotchas this handles:
#   1. Some installs (Homebrew's by default) ship without tkinter at all.
#   2. Apple's system /usr/bin/python3 has tkinter but an ancient Tk 8.5 that
#      renders a blank/broken window on modern macOS.
# So we require tkinter to import AND Tk >= 8.6.
good_py() {
    "$1" -c 'import sys, tkinter; sys.exit(0 if tkinter.TkVersion >= 8.6 else 1)' \
        >/dev/null 2>&1
}

CANDIDATES=(
    python3 python py python3.14 python3.13 python3.12 python3.11
    /opt/homebrew/bin/python3.14 /opt/homebrew/bin/python3 /opt/homebrew/bin/python
    /usr/local/bin/python3.14 /usr/local/bin/python3
    /Library/Frameworks/Python.framework/Versions/3.14/bin/python3
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3
    /usr/bin/python3
)

for py in "${CANDIDATES[@]}"; do
    if command -v "$py" >/dev/null 2>&1 && good_py "$py"; then
        exec "$py" highlighter.py
    fi
done

# Nothing usable found — explain how to fix it and keep the window open.
echo "Could not find a Python 3 with a usable tkinter (Tk >= 8.6)."
echo
echo "If your main Python is Homebrew's, add tkinter to it with:"
echo "    brew install python-tk@3.14        # match your python version"
echo "or install Python from https://www.python.org/downloads/ (Tk included)."
echo
echo "Then double-click this file again."
read -n 1 -s -r -p "Press any key to close..."
echo
