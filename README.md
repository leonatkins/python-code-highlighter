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

1. Paste/type Python in the left pane, or use **File ▸ Open .py…** (`Cmd/Ctrl+O`).
2. The **Preview** (top right) auto-sizes to your code; the **HTML output** box
   below grows to fill the rest.
3. Pick a **Theme** from the dropdown or **View ▸ Theme**. The export uses it.
4. **Copy HTML** or **Save…** the result (both sit above the HTML output).

Python-only. Whitespace and indentation are preserved exactly, and incomplete
snippets still highlight without crashing.

## Themes

Named by background color: **Default Dark**, **Default Light**, **Gray**,
**Solarized Light/Dark**, **Nord**, **Midnight**, **Dracula**, plus two
accessibility themes — **High Contrast** (WCAG-AAA on black) and **Colorblind Safe**
(deuteranopia-friendly Okabe–Ito palette). The status bar shows a live WCAG contrast
readout (`AA ✓`, or how many token colors are dim — the aesthetic themes like
Solarized are intentionally low-contrast; the two accessibility themes always pass).
The input pane's background switches with the theme too, so it matches the preview.

## Accessibility

- **Zoom:** `Cmd/Ctrl` `+` / `-` / `0`, or the **A− / A+** buttons and the slider
  between them — scales the editor, preview, HTML box, and UI together. The code
  panes render a notch smaller than the surrounding UI text at every zoom level.
- **Full keyboard control + menubar** with visible accelerators. Focus outlines show
  which pane is active; `Ctrl+Tab` moves focus out of the editor.
- **Distinct styles** (View menu): renders keywords **bold** and comments *italic* in
  both the preview and the exported HTML, so token types aren't distinguished by
  color alone (WCAG 1.4.1).
- **High-contrast / colorblind themes** and the contrast readout described above.

*Honest limit:* tkinter's screen-reader support is shallow — menus and buttons are
announced by VoiceOver/Narrator, but the text panes' contents largely are not. This
maximizes what Tk can do (keyboard, zoom, contrast, non-color cues, menu semantics);
it isn't a full assistive-tech solution.

## Other features

- **Save to .html** and, via **File ▸ Wrap as full HTML page**, export a complete
  standalone document (affects both Copy and Save so they always match).
- **Line numbers** (View menu) — a non-selectable gutter in the preview and export.
- **Remembers your settings** (theme, toggles, zoom, window size) between launches,
  stored at `~/.config/py-code-highlighter/settings.json` (macOS/Linux) or
  `%APPDATA%\PyCodeHighlighter\settings.json` (Windows).
- Drag-and-drop isn't supported — it would require the third-party `tkinterdnd2`
  package, and this app stays dependency-free. Use **Open .py…** instead.

## Keyboard shortcuts

| Action | macOS | Windows/Linux |
|---|---|---|
| Open .py | `Cmd+O` | `Ctrl+O` |
| Save HTML | `Cmd+S` | `Ctrl+S` |
| Copy HTML | `Cmd+Shift+C` | `Ctrl+Shift+C` |
| Toggle highlighting | `Cmd+L` | `Ctrl+L` |
| Cycle theme | `Cmd+[` / `Cmd+]` | `Ctrl+[` / `Ctrl+]` |
| Zoom in / out / reset | `Cmd` `+` / `-` / `0` | `Ctrl` `+` / `-` / `0` |
