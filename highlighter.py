#!/usr/bin/env python3
"""Python Code -> Highlighted HTML.

Paste Python source, get standalone <pre><code>...</code></pre> HTML with inline
styles (no external CSS/JS) that you can paste anywhere. Dependency-free: uses only
the Python standard library.

Accessibility: text zoom, full keyboard shortcuts + menubar, visible focus rings,
high-contrast and colorblind-safe themes with a live WCAG contrast readout, and an
option to distinguish tokens by weight/slant (not color alone). Plus: open a .py
file, save/copy HTML (snippet or full page), line numbers, and persisted settings.
"""

import builtins
import html
import io
import json
import keyword
import os
import sys
import token as tokmod
import tokenize
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, ttk

_BUILTINS = set(dir(builtins))

# ---------------------------------------------------------------------------
# Themes: one color per token category, plus background / default foreground.
# Insertion order = dropdown order. Keys are the display names.
# ---------------------------------------------------------------------------
THEMES = {
    "Default Dark": {
        "bg": "#272822", "text": "#f8f8f2", "keyword": "#f92672",
        "builtin": "#66d9ef", "string": "#e6db74", "number": "#ae81ff",
        "comment": "#8f9080", "operator": "#f8f8f2", "decorator": "#a6e22e",
    },
    "Default Light": {
        "bg": "#ffffff", "text": "#24292e", "keyword": "#d73a49",
        "builtin": "#6f42c1", "string": "#032f62", "number": "#005cc5",
        "comment": "#6a737d", "operator": "#24292e", "decorator": "#e36209",
    },
    "Gray": {
        "bg": "#e9e9ec", "text": "#2b2b2b", "keyword": "#a626a4",
        "builtin": "#4078f2", "string": "#3f8c3e", "number": "#8a6100",
        "comment": "#6e6e6e", "operator": "#2b2b2b", "decorator": "#9a6700",
    },
    "Solarized Light": {
        "bg": "#fdf6e3", "text": "#586e75", "keyword": "#859900",
        "builtin": "#268bd2", "string": "#2aa198", "number": "#d33682",
        "comment": "#93a1a1", "operator": "#586e75", "decorator": "#b58900",
    },
    "Solarized Dark": {
        "bg": "#002b36", "text": "#93a1a1", "keyword": "#859900",
        "builtin": "#268bd2", "string": "#2aa198", "number": "#d33682",
        "comment": "#657b83", "operator": "#93a1a1", "decorator": "#b58900",
    },
    "Nord": {
        "bg": "#2e3440", "text": "#d8dee9", "keyword": "#81a1c1",
        "builtin": "#88c0d0", "string": "#a3be8c", "number": "#b48ead",
        "comment": "#7b88a1", "operator": "#81a1c1", "decorator": "#ebcb8b",
    },
    "Midnight": {
        "bg": "#0d1117", "text": "#c9d1d9", "keyword": "#ff7b72",
        "builtin": "#d2a8ff", "string": "#a5d6ff", "number": "#79c0ff",
        "comment": "#8b949e", "operator": "#c9d1d9", "decorator": "#ffa657",
    },
    "Dracula": {
        "bg": "#282a36", "text": "#f8f8f2", "keyword": "#ff79c6",
        "builtin": "#8be9fd", "string": "#f1fa8c", "number": "#bd93f9",
        "comment": "#8a94b8", "operator": "#f8f8f2", "decorator": "#50fa7b",
    },
    # Accessibility themes ----------------------------------------------------
    "High Contrast": {
        "bg": "#000000", "text": "#ffffff", "keyword": "#ffd700",
        "builtin": "#00e5ff", "string": "#7fff00", "number": "#ff9edb",
        "comment": "#c8c8c8", "operator": "#ffffff", "decorator": "#ffb000",
    },
    "Colorblind Safe": {  # Okabe-Ito palette (deuteranopia-safe) on light bg
        "bg": "#ffffff", "text": "#000000", "keyword": "#0060a8",
        "builtin": "#0f766e", "string": "#8a5a00", "number": "#a83c7d",
        "comment": "#5a5a5a", "operator": "#000000", "decorator": "#b8480a",
    },
}

DEFAULT_THEME = "Default Dark"

CATEGORIES = ("keyword", "builtin", "string", "number", "comment",
              "operator", "decorator", "text")

# Categories checked against the background for the WCAG contrast readout.
_CONTRAST_CATEGORIES = ("text", "keyword", "builtin", "string", "number",
                        "comment", "decorator")

# Distinct-styles map (category -> (bold, italic)) used when the "distinguish
# tokens by style, not color alone" option is on (WCAG 1.4.1).
STYLE_WEIGHTS = {
    "keyword": (True, False),
    "decorator": (True, False),
    "builtin": (True, False),
    "comment": (False, True),
}


# ---------------------------------------------------------------------------
# WCAG contrast helpers
# ---------------------------------------------------------------------------
def _rel_luminance(hexcolor):
    hexcolor = hexcolor.lstrip("#")
    r, g, b = (int(hexcolor[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(fg, bg):
    """WCAG contrast ratio between two #rrggbb colors (1.0 .. 21.0)."""
    l1, l2 = _rel_luminance(fg), _rel_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def theme_contrast_report(theme_name, threshold=4.5):
    """Return how many token colors fall below the AA threshold vs the bg."""
    theme = THEMES[theme_name]
    bg = theme["bg"]
    return sum(1 for cat in _CONTRAST_CATEGORIES
               if contrast_ratio(theme[cat], bg) < threshold)


# ---------------------------------------------------------------------------
# Tokenizer: source string -> list of (category, text) chunks.
# Whitespace and newlines are preserved verbatim by filling the gaps between
# token positions with the original source text.
# ---------------------------------------------------------------------------
def tokenize_code(code):
    """Return a list of (category, text) pairs covering the whole source."""
    if not code:
        return []

    lines = code.splitlines(keepends=True)

    def slice_source(start, end):
        """Return exact source text between (row, col) positions. 1-based rows."""
        (srow, scol), (erow, ecol) = start, end
        if srow == erow:
            return lines[srow - 1][scol:ecol] if srow - 1 < len(lines) else ""
        parts = [lines[srow - 1][scol:]]
        for r in range(srow, erow - 1):
            parts.append(lines[r])
        if erow - 1 < len(lines):
            parts.append(lines[erow - 1][:ecol])
        return "".join(parts)

    chunks = []
    pos = (1, 0)  # (row, col) of the end of the previous token

    def flush_gap(upto):
        gap = slice_source(pos, upto)
        if gap:
            chunks.append(("text", gap))

    prev_significant = None  # previous non-trivial token string, for decorators
    try:
        tokgen = tokenize.generate_tokens(io.StringIO(code).readline)
        for tok in tokgen:
            ttype, tstring, start, end, _ = tok

            # Fill any whitespace/gap between the last token and this one.
            if start > pos:
                flush_gap(start)

            if ttype in (tokmod.NEWLINE, tokmod.NL, tokmod.INDENT):
                # These carry real whitespace text (newlines / indentation) that
                # must be preserved, but they get no color.
                if tstring:
                    chunks.append(("text", tstring))
                pos = max(pos, end)
                continue
            if ttype in (tokmod.ENCODING, tokmod.ENDMARKER, tokmod.DEDENT):
                # Zero-width / metadata tokens: nothing to emit.
                pos = max(pos, end)
                continue

            cat = classify(ttype, tstring, prev_significant)
            if tstring:
                chunks.append((cat, tstring))
            pos = max(pos, end)

            if tstring.strip():
                prev_significant = tstring
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # Emit whatever source is left un-tokenized as plain text so partial /
        # invalid snippets still render without crashing.
        tail_start = pos
        last_row = len(lines)
        last_col = len(lines[-1]) if lines else 0
        if (last_row, last_col) > tail_start:
            tail = slice_source(tail_start, (last_row, last_col))
            if tail:
                chunks.append(("text", tail))

    return chunks


def classify(ttype, tstring, prev_significant):
    """Map a token to a color category."""
    if ttype == tokmod.COMMENT:
        return "comment"
    if ttype == tokmod.NUMBER:
        return "number"
    if ttype == tokmod.STRING:
        return "string"
    # f-strings are split into FSTRING_START/MIDDLE/END + inner tokens on 3.12+.
    if tokmod.tok_name.get(ttype, "").startswith("FSTRING"):
        return "string"
    if ttype == tokmod.OP:
        return "operator"
    if ttype == tokmod.NAME:
        if keyword.iskeyword(tstring):
            return "keyword"
        # Decorator name: previous significant token was '@'.
        if prev_significant == "@":
            return "decorator"
        if tstring in _BUILTINS and prev_significant != ".":
            return "builtin"
    return "text"


def chunks_to_lines(chunks):
    """Split flat (cat, text) chunks into a list of per-line chunk lists.

    Newlines are consumed as line breaks (not kept in the text), so a token
    spanning multiple lines never has its <span> broken across a newline.
    """
    lines = [[]]
    for cat, text in chunks:
        parts = text.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                lines.append([])
            if part:
                lines[-1].append((cat, part))
    return lines


def to_render_lines(chunks):
    """Lines ready for numbering/rendering: drops a single trailing empty line
    (from a trailing newline) so line counts match an editor's."""
    lines = chunks_to_lines(chunks)
    if len(lines) > 1 and lines[-1] == []:
        lines = lines[:-1]
    return lines


# ---------------------------------------------------------------------------
# HTML generation: standalone <pre><code> with inline styles only.
# ---------------------------------------------------------------------------
def _span_style(theme, cat, distinct):
    style = "color:%s;" % theme[cat]
    if distinct:
        bold, italic = STYLE_WEIGHTS.get(cat, (False, False))
        if bold:
            style += "font-weight:bold;"
        if italic:
            style += "font-style:italic;"
    return style


def build_html(code, theme_name, highlight=True, distinct=False,
               line_numbers=False):
    theme = THEMES[theme_name]

    pre_style = (
        "background:{bg};color:{fg};padding:12px 14px;border-radius:6px;"
        "overflow-x:auto;font-family:'SF Mono',Menlo,Consolas,"
        "'Courier New',monospace;font-size:13px;line-height:1.5;"
        "-moz-tab-size:4;tab-size:4;white-space:pre;"
    ).format(bg=theme["bg"], fg=theme["text"])

    chunks = tokenize_code(code) if highlight else [("text", code)]
    lines = to_render_lines(chunks)
    gutter_w = len(str(max(1, len(lines))))
    gutter_style = ("color:%s;-webkit-user-select:none;user-select:none;"
                    % theme["comment"])

    out = []
    for idx, line in enumerate(lines, start=1):
        seg = []
        if line_numbers:
            num = str(idx).rjust(gutter_w)
            seg.append('<span style="%s">%s │ </span>' % (gutter_style, num))
        for cat, text in line:
            esc = html.escape(text, quote=False)
            if highlight and cat != "text" and cat in theme:
                seg.append('<span style="%s">%s</span>'
                           % (_span_style(theme, cat, distinct), esc))
            else:
                seg.append(esc)
        out.append("".join(seg))

    body = "\n".join(out)
    return '<pre style="{s}"><code>{b}</code></pre>'.format(s=pre_style, b=body)


def wrap_full_page(snippet, theme_name):
    """Wrap a <pre><code> snippet in a complete standalone HTML document."""
    bg = THEMES[theme_name]["bg"]
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>Python code</title>\n</head>\n'
        '<body style="margin:0;padding:16px;background:%s;">\n%s\n</body>\n</html>\n'
        % (bg, snippet))


# ---------------------------------------------------------------------------
# Settings persistence
# ---------------------------------------------------------------------------
def settings_path():
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA") or Path.home())
        return base / "PyCodeHighlighter" / "settings.json"
    return Path.home() / ".config" / "py-code-highlighter" / "settings.json"


def load_settings():
    try:
        with open(settings_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_settings(data):
    try:
        p = settings_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass  # never let a settings write break the app


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
SAMPLE = '''import math


@dataclass
class Circle:
    """A circle with a radius."""
    radius: float = 1.0

    def area(self) -> float:
        # pi * r^2
        return math.pi * self.radius ** 2


for i in range(3):
    c = Circle(radius=i + 1)
    print(f"Area {i}: {c.area():.2f}")
'''

MIN_ZOOM, MAX_ZOOM, BASE_ZOOM = 8, 40, 12
PREVIEW_MIN_LINES = 3
PREVIEW_MAX_LINES = 32
ACCENT = "#4a90d9"


class HighlighterApp:
    def __init__(self, root):
        self.root = root
        settings = load_settings()

        # -- state (seeded from saved settings, validated) -----------------
        theme = settings.get("theme")
        if theme not in THEMES:
            theme = DEFAULT_THEME
        self.theme_name = tk.StringVar(value=theme)
        self.highlight_on = tk.BooleanVar(value=bool(settings.get("highlight", True)))
        self.distinct_styles = tk.BooleanVar(value=bool(settings.get("distinct", False)))
        self.full_page = tk.BooleanVar(value=bool(settings.get("full_page", False)))
        self.line_numbers = tk.BooleanVar(value=bool(settings.get("line_numbers", False)))
        try:
            self.zoom = int(settings.get("zoom", BASE_ZOOM))
        except (TypeError, ValueError):
            self.zoom = BASE_ZOOM
        self.zoom = max(MIN_ZOOM, min(self.zoom, MAX_ZOOM))
        self._current_html = ""

        # -- fonts ---------------------------------------------------------
        fam = _pick_mono_font()
        self.mono_font = tkfont.Font(family=fam, size=self.zoom)
        self.mono_bold = tkfont.Font(family=fam, size=self.zoom, weight="bold")
        self.mono_italic = tkfont.Font(family=fam, size=self.zoom, slant="italic")
        self._ui_fonts = []
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            try:
                f = tkfont.nametofont(name)
                base = f.cget("size") or BASE_ZOOM
                self._ui_fonts.append((f, base))
            except tk.TclError:
                pass

        root.title("Python Code -> Highlighted HTML")
        geo = settings.get("geometry")
        root.geometry(geo if isinstance(geo, str) and "x" in geo else "1160x760")
        root.minsize(820, 520)

        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()
        self.apply_zoom()

        self.input.insert("1.0", SAMPLE)
        self.refresh()

        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- menubar ----------------------------------------------------------
    def _build_menu(self):
        is_mac = sys.platform == "darwin"
        m = "Command" if is_mac else "Control"
        a = "Cmd" if is_mac else "Ctrl"
        self._mod, self._acc = m, a

        menubar = tk.Menu(self.root)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open .py…", command=self.open_file,
                             accelerator=f"{a}+O")
        filemenu.add_command(label="Save HTML…", command=self.save_html,
                             accelerator=f"{a}+S")
        filemenu.add_separator()
        filemenu.add_checkbutton(label="Wrap as full HTML page",
                                 variable=self.full_page,
                                 command=self._on_option_change)
        if not is_mac:
            filemenu.add_separator()
            filemenu.add_command(label="Quit", command=self._on_close,
                                 accelerator=f"{a}+Q")
        menubar.add_cascade(label="File", menu=filemenu)

        viewmenu = tk.Menu(menubar, tearoff=0)
        viewmenu.add_command(label="Zoom In", command=self.zoom_in,
                             accelerator=f"{a}++")
        viewmenu.add_command(label="Zoom Out", command=self.zoom_out,
                             accelerator=f"{a}+-")
        viewmenu.add_command(label="Reset Zoom", command=self.zoom_reset,
                             accelerator=f"{a}+0")
        viewmenu.add_separator()
        viewmenu.add_checkbutton(label="Syntax highlighting",
                                 variable=self.highlight_on,
                                 command=self._on_option_change,
                                 accelerator=f"{a}+L")
        viewmenu.add_checkbutton(label="Distinct styles (bold/italic)",
                                 variable=self.distinct_styles,
                                 command=self._on_option_change)
        viewmenu.add_checkbutton(label="Line numbers",
                                 variable=self.line_numbers,
                                 command=self._on_option_change)
        viewmenu.add_separator()
        thememenu = tk.Menu(viewmenu, tearoff=0)
        for name in THEMES:
            thememenu.add_radiobutton(label=name, value=name,
                                      variable=self.theme_name,
                                      command=self._on_option_change)
        viewmenu.add_cascade(label="Theme", menu=thememenu)
        menubar.add_cascade(label="View", menu=viewmenu)

        self.root.config(menu=menubar)

    # -- layout -----------------------------------------------------------
    def _build_ui(self):
        top = ttk.Frame(self.root, padding=(10, 8))
        top.pack(side="top", fill="x")

        ttk.Label(top, text="Python → HTML Highlighter",
                  font=("TkDefaultFont", 13, "bold")).pack(side="left")
        ttk.Button(top, text="Open .py…", command=self.open_file).pack(
            side="left", padx=(12, 0))

        # Right side (packed right-to-left).
        self.theme_box = ttk.Combobox(
            top, textvariable=self.theme_name, values=list(THEMES),
            state="readonly", width=16)
        self.theme_box.pack(side="right", padx=(0, 4))
        self.theme_box.bind("<<ComboboxSelected>>",
                            lambda e: self._on_option_change())
        ttk.Label(top, text="Theme:").pack(side="right", padx=(12, 6))
        ttk.Checkbutton(top, text="Syntax highlighting",
                        variable=self.highlight_on,
                        command=self._on_option_change).pack(side="right")
        ttk.Button(top, text="A+", width=3, command=self.zoom_in).pack(
            side="right", padx=(12, 2))
        ttk.Button(top, text="A−", width=3, command=self.zoom_out).pack(
            side="right")

        self.status = ttk.Label(self.root, text="", padding=(10, 2), anchor="w")
        self.status.pack(side="bottom", fill="x")

        panes = ttk.PanedWindow(self.root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # Left: input
        left = ttk.Frame(panes)
        ttk.Label(left, text="Paste Python code").pack(anchor="w")
        self.input = tk.Text(left, wrap="none", undo=True, font=self.mono_font,
                             tabstyle="wordprocessor",
                             highlightthickness=2, highlightcolor=ACCENT,
                             highlightbackground="#9aa0a6")
        self.input.pack(fill="both", expand=True)
        self.input.bind("<KeyRelease>", lambda e: self._schedule_refresh())
        self.input.bind("<<Paste>>", lambda e: self._schedule_refresh())
        # Keep Tab for indentation, but let Ctrl+Tab escape for keyboard users.
        self.input.bind("<Control-Tab>", self._focus_next)
        panes.add(left, weight=1)

        # Right: preview (auto-sized to content, top) + raw HTML (fills gap).
        right = ttk.Frame(panes)

        prev_frame = ttk.Frame(right)
        prev_frame.pack(side="top", fill="x")
        ttk.Label(prev_frame, text="Preview").pack(anchor="w")
        self.preview = tk.Text(prev_frame, wrap="none", font=self.mono_font,
                               height=PREVIEW_MIN_LINES, state="disabled",
                               cursor="arrow", highlightthickness=2,
                               highlightcolor=ACCENT,
                               highlightbackground="#9aa0a6")
        self.preview.pack(fill="x")

        html_frame = ttk.Frame(right)
        html_frame.pack(side="top", fill="both", expand=True)
        head = ttk.Frame(html_frame)
        head.pack(fill="x")
        ttk.Label(head, text="HTML output").pack(side="left", anchor="w")
        ttk.Button(head, text="Copy HTML", command=self.copy_html).pack(
            side="right")
        ttk.Button(head, text="Save…", command=self.save_html).pack(
            side="right", padx=(0, 6))
        self.html_out = tk.Text(html_frame, wrap="char", font=self.mono_font,
                                height=6, highlightthickness=2,
                                highlightcolor=ACCENT,
                                highlightbackground="#9aa0a6")
        self.html_out.pack(fill="both", expand=True)
        self.html_out.bind("<Tab>", self._focus_next)
        self.html_out.bind("<Shift-Tab>", self._focus_prev)

        panes.add(right, weight=1)

        self._configure_preview_tags()

    def _configure_preview_tags(self):
        for cat in CATEGORIES:
            self.preview.tag_configure(cat)
        self.preview.tag_configure("gutter")

    def _focus_next(self, event):
        event.widget.tk_focusNext().focus_set()
        return "break"

    def _focus_prev(self, event):
        event.widget.tk_focusPrev().focus_set()
        return "break"

    # -- keyboard shortcuts ----------------------------------------------
    def _bind_shortcuts(self):
        m = self._mod
        b = self.root.bind_all
        b(f"<{m}-o>", lambda e: (self.open_file(), "break")[1])
        b(f"<{m}-s>", lambda e: (self.save_html(), "break")[1])
        b(f"<{m}-l>", lambda e: self._toggle(self.highlight_on))
        b(f"<{m}-Shift-C>", lambda e: (self.copy_html(), "break")[1])
        b(f"<{m}-bracketright>", lambda e: self.cycle_theme(1))
        b(f"<{m}-bracketleft>", lambda e: self.cycle_theme(-1))
        for seq in (f"<{m}-plus>", f"<{m}-equal>"):
            b(seq, lambda e: self.zoom_in())
        b(f"<{m}-minus>", lambda e: self.zoom_out())
        b(f"<{m}-Key-0>", lambda e: self.zoom_reset())

    def _toggle(self, var):
        var.set(not var.get())
        self._on_option_change()
        return "break"

    # -- zoom -------------------------------------------------------------
    def apply_zoom(self):
        for f in (self.mono_font, self.mono_bold, self.mono_italic):
            f.configure(size=self.zoom)
        factor = self.zoom / BASE_ZOOM
        for f, base in self._ui_fonts:
            sign = -1 if base < 0 else 1
            f.configure(size=int(round(abs(base) * factor)) * sign)
        # 4-space tab stops that scale with the font.
        self.input.configure(tabs=(self.mono_font.measure("    "),))

    def zoom_in(self):
        self.zoom = min(self.zoom + 1, MAX_ZOOM)
        self.apply_zoom(); self.refresh(); self._persist()

    def zoom_out(self):
        self.zoom = max(self.zoom - 1, MIN_ZOOM)
        self.apply_zoom(); self.refresh(); self._persist()

    def zoom_reset(self):
        self.zoom = BASE_ZOOM
        self.apply_zoom(); self.refresh(); self._persist()

    def cycle_theme(self, delta):
        names = list(THEMES)
        i = names.index(self.theme_name.get())
        self.theme_name.set(names[(i + delta) % len(names)])
        self._on_option_change()
        return "break"

    # -- render -----------------------------------------------------------
    def _schedule_refresh(self):
        if getattr(self, "_job", None):
            self.root.after_cancel(self._job)
        self._job = self.root.after(120, self.refresh)

    def _on_option_change(self):
        """A toggle/theme changed: re-render and persist (not on every keystroke)."""
        self.refresh()
        self._persist()

    def refresh(self):
        self._job = None
        code = self.input.get("1.0", "end-1c")
        theme = THEMES[self.theme_name.get()]
        highlight = self.highlight_on.get()
        distinct = self.distinct_styles.get()

        # Preview colors + fonts follow the theme / distinct option.
        self.preview.configure(bg=theme["bg"], fg=theme["text"],
                               insertbackground=theme["text"])
        for cat in CATEGORIES:
            font = self.mono_font
            if distinct:
                bold, italic = STYLE_WEIGHTS.get(cat, (False, False))
                if bold:
                    font = self.mono_bold
                elif italic:
                    font = self.mono_italic
            self.preview.tag_configure(cat, foreground=theme.get(cat, theme["text"]),
                                       font=font)
        self.preview.tag_configure("gutter", foreground=theme["comment"],
                                   font=self.mono_font)

        chunks = tokenize_code(code) if highlight else [("text", code)]
        lines = to_render_lines(chunks)
        gutter_w = len(str(max(1, len(lines))))

        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        for idx, line in enumerate(lines, start=1):
            if self.line_numbers.get():
                self.preview.insert("end",
                                    str(idx).rjust(gutter_w) + " │ ", "gutter")
            for cat, text in line:
                self.preview.insert("end", text, cat if highlight else "text")
            self.preview.insert("end", "\n")
        self.preview.delete("end-1c", "end")  # trim final newline
        self.preview.configure(
            height=max(PREVIEW_MIN_LINES, min(len(lines), PREVIEW_MAX_LINES)),
            state="disabled")

        snippet = build_html(code, self.theme_name.get(), highlight, distinct,
                             self.line_numbers.get())
        markup = wrap_full_page(snippet, self.theme_name.get()) \
            if self.full_page.get() else snippet
        self.html_out.delete("1.0", "end")
        self.html_out.insert("1.0", markup)
        self._current_html = markup

        below = theme_contrast_report(self.theme_name.get())
        cs = "AA ✓" if below == 0 else "⚠ %d dim" % below
        self.status.configure(
            text="{} in · {} out · {} · {}pt · contrast {}".format(
                len(code), len(markup),
                "highlighted" if highlight else "plain", self.zoom, cs))

    # -- actions ----------------------------------------------------------
    def copy_html(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self._current_html)
        self.status.configure(text="Copied %d chars of HTML to clipboard ✓"
                              % len(self._current_html))

    def save_html(self):
        path = filedialog.asksaveasfilename(
            title="Save HTML", defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._current_html)
            self.status.configure(text="Saved HTML to %s ✓"
                                  % os.path.basename(path))
        except OSError as e:
            self.status.configure(text="Save failed: %s" % e)

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Open a Python file",
            filetypes=[("Python", "*.py *.pyw"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            self.status.configure(text="Open failed: %s" % e)
            return
        self.input.delete("1.0", "end")
        self.input.insert("1.0", text)
        self.refresh()

    # -- persistence ------------------------------------------------------
    def _collect_settings(self):
        try:
            geometry = self.root.winfo_geometry()
        except tk.TclError:
            geometry = None
        return {
            "theme": self.theme_name.get(),
            "highlight": self.highlight_on.get(),
            "distinct": self.distinct_styles.get(),
            "full_page": self.full_page.get(),
            "line_numbers": self.line_numbers.get(),
            "zoom": self.zoom,
            "geometry": geometry,
        }

    def _persist(self):
        save_settings(self._collect_settings())

    def _on_close(self):
        self._persist()
        self.root.destroy()


def _pick_mono_font():
    """First available monospace font across macOS / Windows / Linux."""
    candidates = ("SF Mono", "Menlo",          # macOS
                  "Consolas", "Cascadia Mono",  # Windows
                  "DejaVu Sans Mono", "Courier New")
    try:
        families = set(tkfont.families())
        for name in candidates:
            if name in families:
                return name
    except Exception:
        pass
    return "Courier"  # Tk's guaranteed generic monospace


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    HighlighterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
