#!/usr/bin/env python3
"""Python Code -> Highlighted HTML.

Paste Python source, get standalone <pre><code>...</code></pre> HTML with inline
styles (no external CSS/JS) that you can paste anywhere. Dependency-free: uses only
the Python standard library (tkinter, tokenize, keyword, builtins, html, io).
"""

import builtins
import html
import io
import keyword
import token as tokmod
import tokenize
import tkinter as tk
from tkinter import ttk

_BUILTINS = set(dir(builtins))

# ---------------------------------------------------------------------------
# Themes: one color per token category, plus background / default foreground.
# ---------------------------------------------------------------------------
THEMES = {
    "light": {
        "bg": "#ffffff",
        "text": "#24292e",
        "keyword": "#d73a49",
        "builtin": "#6f42c1",
        "string": "#032f62",
        "number": "#005cc5",
        "comment": "#6a737d",
        "operator": "#24292e",
        "decorator": "#e36209",
    },
    "dark": {
        "bg": "#272822",
        "text": "#f8f8f2",
        "keyword": "#f92672",
        "builtin": "#66d9ef",
        "string": "#e6db74",
        "number": "#ae81ff",
        "comment": "#75715e",
        "operator": "#f8f8f2",
        "decorator": "#a6e22e",
    },
}

CATEGORIES = ("keyword", "builtin", "string", "number", "comment",
              "operator", "decorator", "text")


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
            elif start < pos:
                # Overlap (rare, e.g. some synthesized tokens) -> skip safely.
                pass

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


# ---------------------------------------------------------------------------
# HTML generation: standalone <pre><code> with inline styles only.
# ---------------------------------------------------------------------------
def build_html(code, theme_name):
    theme = THEMES[theme_name]
    chunks = tokenize_code(code)

    pre_style = (
        "background:{bg};color:{fg};padding:12px 14px;border-radius:6px;"
        "overflow-x:auto;font-family:'SF Mono',Menlo,Consolas,"
        "'Courier New',monospace;font-size:13px;line-height:1.5;"
        "-moz-tab-size:4;tab-size:4;white-space:pre;"
    ).format(bg=theme["bg"], fg=theme["text"])

    parts = []
    for cat, text in chunks:
        esc = html.escape(text, quote=False)
        if cat == "text" or cat not in theme:
            parts.append(esc)
        else:
            parts.append('<span style="color:{c}">{t}</span>'.format(
                c=theme[cat], t=esc))

    body = "".join(parts)
    return '<pre style="{s}"><code>{b}</code></pre>'.format(s=pre_style, b=body)


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


class HighlighterApp:
    def __init__(self, root):
        self.root = root
        self.theme_name = tk.StringVar(value="light")
        root.title("Python Code -> Highlighted HTML")
        root.geometry("1100x720")
        root.minsize(760, 480)

        self._build_ui()
        self.input.insert("1.0", SAMPLE)
        self.refresh()

    # -- layout -----------------------------------------------------------
    def _build_ui(self):
        top = ttk.Frame(self.root, padding=(10, 8))
        top.pack(side="top", fill="x")

        ttk.Label(top, text="Python → HTML Highlighter",
                  font=("TkDefaultFont", 13, "bold")).pack(side="left")

        ttk.Button(top, text="Copy HTML", command=self.copy_html).pack(
            side="right")

        ttk.Radiobutton(top, text="Dark", value="dark",
                        variable=self.theme_name,
                        command=self.refresh).pack(side="right", padx=(0, 12))
        ttk.Radiobutton(top, text="Light", value="light",
                        variable=self.theme_name,
                        command=self.refresh).pack(side="right", padx=(0, 4))
        ttk.Label(top, text="Theme:").pack(side="right", padx=(0, 6))

        self.status = ttk.Label(self.root, text="", padding=(10, 2),
                                anchor="w")
        self.status.pack(side="bottom", fill="x")

        panes = ttk.PanedWindow(self.root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        mono = (_pick_mono_font(), 12)

        # Left: input
        left = ttk.Frame(panes)
        ttk.Label(left, text="Paste Python code").pack(anchor="w")
        self.input = tk.Text(left, wrap="none", undo=True, font=mono,
                             tabs="4c", tabstyle="wordprocessor")
        self.input.pack(fill="both", expand=True)
        self.input.bind("<KeyRelease>", lambda e: self._schedule_refresh())
        self.input.bind("<<Paste>>", lambda e: self._schedule_refresh())
        panes.add(left, weight=1)

        # Right: preview (top) + raw html (bottom)
        right = ttk.PanedWindow(panes, orient="vertical")

        prev_frame = ttk.Frame(right)
        ttk.Label(prev_frame, text="Preview").pack(anchor="w")
        self.preview = tk.Text(prev_frame, wrap="none", font=mono,
                               state="disabled", cursor="arrow")
        self.preview.pack(fill="both", expand=True)
        right.add(prev_frame, weight=1)

        html_frame = ttk.Frame(right)
        ttk.Label(html_frame, text="HTML output").pack(anchor="w")
        self.html_out = tk.Text(html_frame, wrap="char", font=mono, height=8)
        self.html_out.pack(fill="both", expand=True)
        right.add(html_frame, weight=1)

        panes.add(right, weight=1)

        self._configure_preview_tags()

    def _configure_preview_tags(self):
        for cat in CATEGORIES:
            self.preview.tag_configure(cat)

    # -- behavior ---------------------------------------------------------
    def _schedule_refresh(self):
        if getattr(self, "_job", None):
            self.root.after_cancel(self._job)
        self._job = self.root.after(120, self.refresh)

    def refresh(self):
        self._job = None
        code = self.input.get("1.0", "end-1c")
        theme = THEMES[self.theme_name.get()]

        # Preview widget colors follow the theme.
        self.preview.configure(bg=theme["bg"], fg=theme["text"],
                               insertbackground=theme["text"])
        for cat in CATEGORIES:
            self.preview.tag_configure(cat, foreground=theme.get(cat,
                                       theme["text"]))

        chunks = tokenize_code(code)

        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        for cat, text in chunks:
            self.preview.insert("end", text, cat)
        self.preview.configure(state="disabled")

        markup = build_html(code, self.theme_name.get())
        self.html_out.delete("1.0", "end")
        self.html_out.insert("1.0", markup)
        self._current_html = markup

        self.status.configure(
            text="{} chars in · {} chars of HTML out".format(
                len(code), len(markup)))

    def copy_html(self):
        markup = getattr(self, "_current_html", "")
        self.root.clipboard_clear()
        self.root.clipboard_append(markup)
        self.status.configure(text="Copied {} chars of HTML to clipboard "
                              "✓".format(len(markup)))


def _pick_mono_font():
    """First available monospace font across macOS / Windows / Linux."""
    candidates = ("SF Mono", "Menlo",          # macOS
                  "Consolas", "Cascadia Mono",  # Windows
                  "DejaVu Sans Mono", "Courier New")
    try:
        import tkinter.font as tkfont
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
