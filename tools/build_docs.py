#!/usr/bin/env python3
"""
build_docs.py — Convert the ULTIMATE MARRIAGE GUIDE markdown files into
styled HTML and print-ready PDF, using a pure-Python toolchain
(markdown + reportlab). No pandoc / wkhtmltopdf / weasyprint required.

Usage:
    python3 tools/build_docs.py FILE.md [FILE2.md ...]
    python3 tools/build_docs.py --all
"""

from __future__ import annotations

import html as html_lib
import os
import re
import sys
import unicodedata

import markdown as md_lib
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, KeepTogether, PageBreak, Preformatted,
)

# --------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONTS = {
    "Body": ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf",
             "DejaVuSans-Oblique.ttf", "DejaVuSans-BoldOblique.ttf"),
    "Mono": ("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf",
             "DejaVuSansMono-Oblique.ttf", "DejaVuSansMono-BoldOblique.ttf"),
}


def register_fonts() -> None:
    """Register DejaVu faces, falling back to the regular/bold cuts when the
    oblique files are not shipped by the distro (common on slim images)."""
    for family, (reg, bold, ital, bi) in FONTS.items():
        def path_or(candidate, fallback):
            p = os.path.join(FONT_DIR, candidate)
            return p if os.path.exists(p) else os.path.join(FONT_DIR, fallback)

        pdfmetrics.registerFont(TTFont(family, path_or(reg, reg)))
        pdfmetrics.registerFont(TTFont(family + "-Bold", path_or(bold, reg)))
        pdfmetrics.registerFont(TTFont(family + "-Italic", path_or(ital, reg)))
        pdfmetrics.registerFont(TTFont(family + "-BoldItalic", path_or(bi, bold)))
        pdfmetrics.registerFontFamily(
            family, normal=family, bold=family + "-Bold",
            italic=family + "-Italic", boldItalic=family + "-BoldItalic")


# --------------------------------------------------------------------------
# Text cleaning
# --------------------------------------------------------------------------
EMOJI_RE = re.compile(
    "[" "\U0001F000-\U0001FAFF" "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF" "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF" "\U0000FE00-\U0000FE0F"
    "\U0001F900-\U0001F9FF" "\U00002700-\U000027BF" "\U000024C2"
    "]+", flags=re.UNICODE)

ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")

# Symbols DejaVu covers; keep these, they read well in print.
KEEP_MAP = {
    "\ufdfa": " (peace be upon him)",  # ﷺ — not in DejaVu, renders as tofu
    "\ufdfd": "Bismillah",             # ﷽
    "✅": "[YES]", "❌": "[NO]", "⚠️": "!", "⚠": "!", "☠️": "(!)",
    "☐": "[  ]", "🚩": ">", "→": "->", "•": "\u2022",
    "├": "|", "└": "|", "│": "|", "─": "-", "☑": "[x]",
}


_COVERAGE: set[int] | None = None


def _font_coverage() -> set:
    """Codepoints the body font can actually draw, so nothing renders as tofu."""
    global _COVERAGE
    if _COVERAGE is None:
        try:
            from fontTools.ttLib import TTFont as FTFont
            f = FTFont(os.path.join(FONT_DIR, "DejaVuSans.ttf"), lazy=True)
            _COVERAGE = set(f.getBestCmap().keys())
            f.close()
        except Exception:
            _COVERAGE = set()
    return _COVERAGE


def clean_for_pdf(text: str) -> str:
    for k, v in KEEP_MAP.items():
        text = text.replace(k, v)
    text = EMOJI_RE.sub("", text)
    cov = _font_coverage()
    if cov:
        text = "".join(
            c for c in text
            if ord(c) in cov or c in "\n\t" or ARABIC_RE.match(c)
            or unicodedata.category(c) == "Mn"
        )
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def is_mostly_arabic(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    return sum(1 for c in letters if ARABIC_RE.match(c)) / len(letters) > 0.4


def inline_md_to_rl(text: str) -> str:
    """Convert inline markdown to reportlab mini-HTML."""
    text = clean_for_pdf(text)
    text = html_lib.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r'<font face="Mono" size="8.5">\1</font>', text)
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#2471a3">\1</link>', text)
    return balance_tags(text)


def balance_tags(text: str) -> str:
    """ReportLab's mini-HTML parser rejects improperly nested/unclosed tags,
    which hand-written markdown produces routinely (e.g. **a <i>b**</i>).
    Re-emit the inline tags in strictly nested order."""
    tokens = re.split(r"(</?(?:b|i|u|super|sub)>)", text)
    out, stack = [], []
    for tok in tokens:
        m = re.fullmatch(r"<(/?)(b|i|u|super|sub)>", tok)
        if not m:
            out.append(tok)
            continue
        closing, tag = bool(m.group(1)), m.group(2)
        if not closing:
            stack.append(tag)
            out.append(tok)
        else:
            if tag not in stack:
                continue  # stray close tag -> drop
            # close everything opened after `tag`, then reopen them
            reopen = []
            while stack:
                top = stack.pop()
                out.append(f"</{top}>")
                if top == tag:
                    break
                reopen.append(top)
            for t in reversed(reopen):
                out.append(f"<{t}>")
                stack.append(t)
    while stack:
        out.append(f"</{stack.pop()}>")
    return "".join(out)


# --------------------------------------------------------------------------
# Styles
# --------------------------------------------------------------------------
def build_styles():
    ss = getSampleStyleSheet()
    S = {}
    S["title"] = ParagraphStyle("title", parent=ss["Normal"], fontName="Body-Bold",
                                fontSize=24, leading=30, alignment=TA_CENTER,
                                textColor=colors.HexColor("#1a3d5c"), spaceAfter=14)
    S["h1"] = ParagraphStyle("h1", parent=ss["Normal"], fontName="Body-Bold",
                             fontSize=19, leading=24, textColor=colors.HexColor("#1a3d5c"),
                             spaceBefore=20, spaceAfter=10)
    S["h2"] = ParagraphStyle("h2", parent=ss["Normal"], fontName="Body-Bold",
                             fontSize=15, leading=20, textColor=colors.HexColor("#21618c"),
                             spaceBefore=16, spaceAfter=8)
    S["h3"] = ParagraphStyle("h3", parent=ss["Normal"], fontName="Body-Bold",
                             fontSize=12.5, leading=17, textColor=colors.HexColor("#2874a6"),
                             spaceBefore=12, spaceAfter=6)
    S["h4"] = ParagraphStyle("h4", parent=ss["Normal"], fontName="Body-BoldItalic",
                             fontSize=11, leading=15, textColor=colors.HexColor("#34495e"),
                             spaceBefore=10, spaceAfter=5)
    S["body"] = ParagraphStyle("body", parent=ss["Normal"], fontName="Body",
                               fontSize=9.8, leading=14.5, alignment=TA_JUSTIFY,
                               textColor=colors.HexColor("#222222"), spaceAfter=6)
    S["quote"] = ParagraphStyle("quote", parent=S["body"], fontName="Body-Italic",
                                leftIndent=14, rightIndent=8, spaceBefore=6, spaceAfter=6,
                                textColor=colors.HexColor("#3d4f5c"),
                                borderColor=colors.HexColor("#7fb3d5"),
                                borderWidth=0, borderPadding=0)
    S["li"] = ParagraphStyle("li", parent=S["body"], leftIndent=16,
                             bulletIndent=6, spaceAfter=3, alignment=0)
    S["li2"] = ParagraphStyle("li2", parent=S["li"], leftIndent=32, bulletIndent=22)
    S["cell"] = ParagraphStyle("cell", parent=ss["Normal"], fontName="Body",
                               fontSize=8.4, leading=11.5,
                               textColor=colors.HexColor("#222222"))
    S["cellh"] = ParagraphStyle("cellh", parent=S["cell"], fontName="Body-Bold",
                                textColor=colors.white)
    return S


# --------------------------------------------------------------------------
# Markdown -> flowables
# --------------------------------------------------------------------------
def split_row(line: str):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def is_sep_row(line: str) -> bool:
    return bool(re.match(r"^\s*\|?[\s:|-]+\|[\s:|-]*$", line)) and "-" in line


def make_table(rows, S, avail_width):
    if not rows:
        return None
    ncols = max(len(r) for r in rows)
    data = []
    for i, row in enumerate(rows):
        row = row + [""] * (ncols - len(row))
        style = S["cellh"] if i == 0 else S["cell"]
        data.append([Paragraph(inline_md_to_rl(c) or "&nbsp;", style) for c in row])

    # width proportional to content, clamped
    weights = []
    for c in range(ncols):
        w = max(len(clean_for_pdf(rows[r][c])) if c < len(rows[r]) else 0
                for r in range(len(rows)))
        weights.append(max(6, min(w, 60)))
    total = sum(weights)
    widths = [avail_width * w / total for w in weights]

    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#21618c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9c4cc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f2f6f9")]),
    ]))
    return t


def md_to_flowables(text: str, S, avail_width):
    flow = []
    lines = text.split("\n")
    i = 0
    para_buf = []
    quote_buf = []

    def flush_para():
        nonlocal para_buf
        if para_buf:
            joined = " ".join(para_buf).strip()
            para_buf = []
            if joined and not is_mostly_arabic(joined):
                flow.append(Paragraph(inline_md_to_rl(joined), S["body"]))

    def flush_quote():
        nonlocal quote_buf
        if quote_buf:
            joined = " ".join(quote_buf).strip()
            quote_buf = []
            if joined and not is_mostly_arabic(joined):
                flow.append(HRFlowable(width="35%", thickness=1.2, spaceBefore=3,
                                       spaceAfter=3, color=colors.HexColor("#7fb3d5"),
                                       hAlign="LEFT"))
                flow.append(Paragraph(inline_md_to_rl(joined), S["quote"]))

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        # fenced code
        if stripped.startswith("```"):
            flush_para(); flush_quote()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(clean_for_pdf(lines[i]))
                i += 1
            i += 1
            if buf:
                flow.append(Preformatted("\n".join(buf),
                            ParagraphStyle("code", fontName="Mono", fontSize=7.4,
                                           leading=9.6,
                                           textColor=colors.HexColor("#1c2833"),
                                           backColor=colors.HexColor("#f4f6f7"),
                                           borderPadding=5, leftIndent=4)))
                flow.append(Spacer(1, 6))
            continue

        # blank
        if not stripped:
            flush_para(); flush_quote()
            i += 1
            continue

        # horizontal rule
        if re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", line):
            flush_para(); flush_quote()
            flow.append(Spacer(1, 4))
            flow.append(HRFlowable(width="100%", thickness=0.8,
                                   color=colors.HexColor("#aab7c4")))
            flow.append(Spacer(1, 6))
            i += 1
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush_para(); flush_quote()
            level = len(m.group(1))
            txt = m.group(2).strip()
            key = {1: "h1", 2: "h2", 3: "h3"}.get(level, "h4")
            if level == 1:
                flow.append(Spacer(1, 8))
            flow.append(Paragraph(inline_md_to_rl(txt), S[key]))
            if level <= 2:
                flow.append(HRFlowable(width="100%", thickness=1.1,
                                       color=colors.HexColor("#7fb3d5"),
                                       spaceBefore=2, spaceAfter=6))
            i += 1
            continue

        # table
        if stripped.startswith("|") and i + 1 < len(lines) and is_sep_row(lines[i + 1]):
            flush_para(); flush_quote()
            rows = [split_row(stripped)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            t = make_table(rows, S, avail_width)
            if t:
                flow.append(Spacer(1, 4))
                flow.append(t)
                flow.append(Spacer(1, 8))
            continue

        # blockquote
        if stripped.startswith(">"):
            flush_para()
            content = stripped.lstrip(">").strip()
            if content:
                quote_buf.append(content)
            i += 1
            continue

        # list item
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if m:
            flush_para(); flush_quote()
            indent, marker, content = m.group(1), m.group(2), m.group(3)
            style = S["li2"] if len(indent) >= 2 else S["li"]
            bullet = "\u2022" if marker in "-*+" else marker
            if not is_mostly_arabic(content):
                flow.append(Paragraph(inline_md_to_rl(content), style,
                                      bulletText=clean_for_pdf(bullet) or "\u2022"))
            i += 1
            continue

        flush_quote()
        para_buf.append(stripped)
        i += 1

    flush_para(); flush_quote()
    return flow


# --------------------------------------------------------------------------
# Page furniture
# --------------------------------------------------------------------------
class GuideDoc(BaseDocTemplate):
    def __init__(self, path, running_title, **kw):
        super().__init__(path, pagesize=A4,
                         leftMargin=20 * mm, rightMargin=20 * mm,
                         topMargin=20 * mm, bottomMargin=18 * mm, **kw)
        self.running_title = running_title
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="body")
        self.addPageTemplates([PageTemplate(id="main", frames=[frame],
                                            onPage=self.decorate)])

    def decorate(self, canvas, doc):
        canvas.saveState()
        page = canvas.getPageNumber()
        if page > 1:
            canvas.setFont("Body", 7.5)
            canvas.setFillColor(colors.HexColor("#8899a6"))
            canvas.drawString(doc.leftMargin, A4[1] - 13 * mm, self.running_title)
            canvas.setStrokeColor(colors.HexColor("#d5dbdb"))
            canvas.setLineWidth(0.4)
            canvas.line(doc.leftMargin, A4[1] - 15 * mm,
                        A4[0] - doc.rightMargin, A4[1] - 15 * mm)
            canvas.drawCentredString(A4[0] / 2, 11 * mm, str(page))
        canvas.restoreState()


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{ --accent:#21618c; --accent-light:#7fb3d5; --ink:#222; }}
  body {{ font-family: Georgia, 'Times New Roman', serif; line-height:1.65;
          max-width: 860px; margin: 0 auto; padding: 32px 24px; color: var(--ink);
          background:#fff; }}
  h1,h2,h3,h4,h5,h6 {{ color:#1a3d5c; line-height:1.3; margin-top:1.6em; margin-bottom:.5em; }}
  h1 {{ font-size:2.1em; border-bottom:3px solid var(--accent); padding-bottom:.25em; }}
  h2 {{ font-size:1.55em; border-bottom:2px solid var(--accent-light); padding-bottom:.2em; }}
  h3 {{ font-size:1.22em; color: var(--accent); }}
  h4 {{ font-size:1.05em; color:#34495e; }}
  p {{ margin:.75em 0; text-align: justify; }}
  ul,ol {{ margin:.7em 0; padding-left:1.9em; }}
  li {{ margin:.28em 0; }}
  blockquote {{ border-left:4px solid var(--accent-light); background:#f4f8fb;
                margin:1em 0; padding:.7em 1.1em; color:#3d4f5c; font-style:italic;
                border-radius:0 4px 4px 0; }}
  blockquote strong {{ font-style:normal; }}
  table {{ border-collapse:collapse; width:100%; margin:1.2em 0; font-size:.94em; }}
  th,td {{ border:1px solid #cfd8dc; padding:9px 11px; text-align:left;
           vertical-align:top; }}
  th {{ background: var(--accent); color:#fff; font-weight:bold; }}
  tr:nth-child(even) td {{ background:#f4f8fb; }}
  code {{ font-family:'DejaVu Sans Mono',Consolas,monospace; background:#eef2f5;
          padding:.12em .38em; border-radius:3px; font-size:.9em; }}
  pre {{ background:#f4f6f7; padding:1em; border-radius:5px; overflow-x:auto;
         font-size:.85em; line-height:1.45; border:1px solid #e0e6ea; }}
  pre code {{ background:none; padding:0; }}
  hr {{ border:none; border-top:2px solid var(--accent-light); margin:2.2em 0; }}
  a {{ color:#2471a3; }}
  @media print {{
    body {{ max-width:none; padding:0; font-size:11pt; }}
    @page {{ size: A4; margin: 18mm; }}
    h1,h2,h3 {{ page-break-after: avoid; }}
    table,blockquote,pre {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
{content}
</body>
</html>
"""


def build_html(md_text: str, title: str) -> str:
    body = md_lib.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list", "toc", "nl2br"],
    )
    return HTML_TEMPLATE.format(title=html_lib.escape(title), content=body)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def build(md_path: str) -> None:
    base = os.path.splitext(md_path)[0]
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()

    first_heading = next((l.lstrip("# ").strip() for l in md_text.split("\n")
                          if l.startswith("# ")), os.path.basename(base))
    title = clean_for_pdf(first_heading)

    html_path = base + ".html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html(md_text, title))
    print(f"  HTML -> {html_path} ({os.path.getsize(html_path)//1024} KB)")

    register_fonts()
    S = build_styles()
    pdf_path = base + ".pdf"
    doc = GuideDoc(pdf_path, running_title=title)
    flow = md_to_flowables(md_text, S, doc.width)
    doc.build(flow)
    print(f"  PDF  -> {pdf_path} ({os.path.getsize(pdf_path)//1024} KB)")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    if args == ["--all"]:
        args = sorted(f for f in os.listdir(".")
                      if f.startswith("ULTIMATE_MARRIAGE_GUIDE") and f.endswith(".md"))
    for path in args:
        print(f"Building {path} ...")
        build(path)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
