# Build & Conversion Guide

The PDFs in this repository are **generated automatically** by `tools/build_docs.py` using a pure-Python toolchain. No pandoc, wkhtmltopdf, WeasyPrint, or Chromium required.

---

## ✅ Method 1: The Included Builder (Recommended)

### Install dependencies

```bash
pip install markdown reportlab fonttools
# On Debian/Ubuntu with an externally managed Python:
pip install --break-system-packages markdown reportlab fonttools
```

You also need the DejaVu fonts (present by default on most Linux systems):

```bash
sudo apt-get install -y fonts-dejavu-core   # if missing
```

### Build

```bash
# Build every ULTIMATE_MARRIAGE_GUIDE*.md file in the repo
python3 tools/build_docs.py --all

# Build a specific file
python3 tools/build_docs.py ULTIMATE_MARRIAGE_GUIDE_COMPLETE_Parts_1-5.md
```

### Output

For each `NAME.md`, the builder writes:

- `NAME.html` — styled, responsive, print-optimized HTML
- `NAME.pdf` — A4, paginated, with running headers and page numbers

### What the builder handles

| Feature | Support |
|---------|---------|
| Headings (H1–H6) with rules | ✅ |
| Bold / italic / inline code / links | ✅ |
| Bulleted & numbered lists (nested) | ✅ |
| Markdown tables with zebra striping and header repeat across pages | ✅ |
| Blockquotes rendered as styled pull-quotes | ✅ |
| Fenced code blocks (e.g. the Crisis Decision Tree) | ✅ |
| Horizontal rules | ✅ |
| Emoji stripping for print (kept in HTML) | ✅ |
| Glyph-safety — ﷺ transliterated to "(peace be upon him)" instead of a tofu box | ✅ |
| Malformed inline HTML auto-repaired before PDF layout | ✅ |
| A4 pagination, running header, centered page numbers | ✅ |

---

## 🌐 Method 2: Browser Print to PDF

Works everywhere, no installs. The HTML files include a `@media print` stylesheet with A4 sizing and page-break control.

1. Open `ULTIMATE_MARRIAGE_GUIDE_COMPLETE_Parts_1-5.html` in Chrome, Edge, Firefox, or Safari.
2. Press `Ctrl + P` (Windows/Linux) or `Cmd + P` (Mac).
3. Set destination to **Save as PDF**.
4. Recommended settings: A4, default margins, **Background graphics ON** (so table headers keep their color).
5. Save.

---

## 📄 Method 3: Pandoc

```bash
pandoc ULTIMATE_MARRIAGE_GUIDE_COMPLETE_Parts_1-5.md \
  -o guide.pdf \
  --pdf-engine=xelatex \
  -V mainfont="DejaVu Sans" \
  -V geometry:margin=20mm \
  --toc
```

Requires a TeX distribution. Use a Unicode-capable font, since the source contains Arabic and typographic characters.

---

## 🖨️ Method 4: wkhtmltopdf

```bash
wkhtmltopdf --enable-local-file-access \
  --page-size A4 --margin-top 18mm --margin-bottom 18mm \
  --footer-center "[page]" \
  ULTIMATE_MARRIAGE_GUIDE_COMPLETE_Parts_1-5.html guide.pdf
```

---

## 🧩 Troubleshooting

| Problem | Fix |
|---------|-----|
| `TTFError: Can't open file ... DejaVuSans-Oblique.ttf` | Handled automatically — the builder falls back to the regular cut when oblique faces aren't installed |
| `error: externally-managed-environment` | Add `--break-system-packages` to pip, or use a virtualenv |
| Boxes/tofu in the PDF | The builder filters to the font's actual coverage; if you swap fonts, update `FONT_DIR` in `tools/build_docs.py` |
| Arabic script missing from the PDF | Intentional — ReportLab lacks RTL shaping, so Arabic-only lines are omitted from the PDF while transliterations and translations are retained. Full Arabic is preserved in the `.md` and `.html` |
| Table too wide / squashed | Column widths are content-proportional; shorten the longest header cell in the markdown |

---

## 📊 Current Build Output

| Source | HTML | PDF | Pages |
|--------|------|-----|-------|
| `ULTIMATE_MARRIAGE_GUIDE_COMPLETE_Parts_1-5.md` | 678 KB | 721 KB | **230** |
| `ULTIMATE_MARRIAGE_GUIDE_Parts_1-3.md` | 440 KB | 450 KB | 145 |
| `ULTIMATE_MARRIAGE_GUIDE_Part_4.md` | 135 KB | 203 KB | 47 |
| `ULTIMATE_MARRIAGE_GUIDE_Part_5.md` | 106 KB | 154 KB | 39 |
