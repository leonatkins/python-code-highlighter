# Python Code → Highlighted HTML

A tiny, dependency-free desktop app. Paste Python code, get standalone
`<pre><code>…</code></pre>` HTML with **inline styles** (no external CSS or JS) that
you can paste into a blog, docs, CMS, or any web page and it renders with syntax
highlighting.

## Launch

The app itself (`highlighter.py`) is the same on every platform — only the
double-click launcher differs.

### macOS
- **Finder:** double-click `Launch Highlighter.command`.
  - The first time, macOS Gatekeeper may say it's from an *unidentified developer*.
    Right-click the file → **Open** → **Open** once to whitelist it. After that,
    double-click works normally.
- **Terminal:** `python3 highlighter.py`

### Windows
- **Explorer:** double-click `Launch Highlighter.bat`.
  - If Windows SmartScreen shows a warning, click **More info → Run anyway** (once).
- **Command Prompt / PowerShell:** `python highlighter.py` (or `py highlighter.py`).

Requires Python 3 with tkinter — bundled with the standard installers from
[python.org](https://www.python.org/downloads/) on both macOS and Windows. On the
Windows installer, tick **"Add python.exe to PATH"**. No `pip install` needed.

**Note on tkinter:** the macOS launcher auto-selects a Python with a *usable*
tkinter — it requires **Tk ≥ 8.6**, which skips two common traps:

- Homebrew's `python3` ships without tkinter by default. Add it with
  `brew install python-tk@3.14` (match your Python version).
- Apple's system `/usr/bin/python3` has tkinter but an ancient **Tk 8.5** that
  renders a blank/broken window — the launcher deliberately ignores it.

If nothing usable is found, the launcher prints these same instructions.

## Use

1. Paste (or type) Python code in the left pane.
2. The **Preview** (top right) auto-sizes to your code; the **HTML output** box
   below it grows to fill the rest of the panel.
3. Pick a **Theme** from the dropdown — Default Dark, Default Light, Gray,
   Solarized Light/Dark, Nord, Midnight, or Dracula (named by background color).
   The export uses the selected theme.
4. Toggle **Syntax highlighting** off for a plain monochrome code block, on for
   colors.
5. Click **Copy HTML** (next to the HTML output) and paste the HTML wherever you
   want.

Python-only. Whitespace and indentation are preserved exactly, and incomplete
snippets still highlight without crashing.
