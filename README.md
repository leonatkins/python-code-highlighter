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

## Use

1. Paste (or type) Python code in the left pane.
2. The **Preview** shows the highlighted result; the **HTML output** box shows the
   raw HTML.
3. Pick **Light** or **Dark** — the export uses the selected theme.
4. Click **Copy HTML** and paste the HTML wherever you want.

Python-only. Whitespace and indentation are preserved exactly, and incomplete
snippets still highlight without crashing.
