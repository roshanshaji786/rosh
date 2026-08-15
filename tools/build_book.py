#!/usr/bin/env python3
"""
build_book.py — Produce the polished, print-ready FINAL EDITION PDF of
THE ULTIMATE GUIDE TO A SUCCESSFUL MARRIAGE.

Adds, on top of tools/build_docs.py:
  * a designed cover page
  * a title page, copyright / disclaimer page and a "How to Use" page
  * an auto-generated Table of Contents with REAL page numbers (two-pass build)
  * full-page part dividers
  * clickable PDF bookmarks (outline pane) for every part, chapter and appendix
  * running headers that track the current chapter
  * page numbers suppressed on front matter and divider pages

Usage:
    python3 tools/build_book.py SOURCE.md OUTPUT.pdf
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer,
    PageBreak, HRFlowable, Flowable,
)
from reportlab.platypus.tableofcontents import TableOfContents

import build_docs as bd

PAGE_W, PAGE_H = A4

NAVY = colors.HexColor("#12324f")
BLUE = colors.HexColor("#21618c")
LIGHT = colors.HexColor("#7fb3d5")
GOLD = colors.HexColor("#b9922f")
MUTED = colors.HexColor("#8899a6")


# --------------------------------------------------------------------------
# Heading classification (drives TOC + bookmarks)
# --------------------------------------------------------------------------
RE_PART = re.compile(r"^PART\s+([0-9]+)\s*[:\u2013-]\s*(.+)$", re.I)
RE_CHAPTER = re.compile(r"^CHAPTER\s+([0-9]+)\s*[:\u2013-]\s*(.+)$", re.I)
RE_APPENDIX = re.compile(r"^APPENDIX\s+([A-Z])\s*[:\u2013-]\s*(.+)$", re.I)


def classify(text: str, hashes: int = 1):
    """Return (toc_level, label) for a heading, or (None, None) to skip.

    `hashes` is the markdown heading depth. Parts are H1 only and chapters /
    appendices H1-H2, so the source document's own contents listing (which uses
    H3) is not mistaken for real structure.
    """
    t = bd.clean_for_pdf(re.sub(r"[*_`]", "", text))
    # emoji stripping can leave zero-width joiners / variation selectors behind
    t = re.sub(r"[\u200b-\u200f\ufe0e\ufe0f\u2060]", "", t).strip()
    if hashes == 1:
        m = RE_PART.match(t)
        # the real part openers are bare titles; "PART 1: ACTION PLAN &
        # WORKSHEETS" and "CONCLUSION OF PART 1" are in-body sections
        if m and not re.search(r"ACTION PLAN|WORKSHEET|CONCLUSION", t, re.I):
            return 0, f"Part {m.group(1)}: {m.group(2).strip()}"
    if hashes <= 2:
        m = RE_CHAPTER.match(t)
        if m:
            return 1, f"Chapter {m.group(1)}: {m.group(2).strip()}"
        m = RE_APPENDIX.match(t)
        if m:
            return 1, f"Appendix {m.group(1)}: {m.group(2).strip()}"
    return None, None


# --------------------------------------------------------------------------
# Front matter flowables
# --------------------------------------------------------------------------
class CoverPage(Flowable):
    """Full-bleed designed cover drawn directly on the canvas."""

    def __init__(self, meta):
        super().__init__()
        self.meta = meta
        self.width, self.height = 0, 0

    def wrap(self, aw, ah):
        self._aw, self._ah = aw, ah
        return aw, ah

    def draw(self):
        c = self.canv
        m = self.meta
        c.saveState()
        # move the origin from wherever the flowable landed back to (0, 0)
        x, y = c.absolutePosition(0, 0)
        c.translate(-x, -y)

        # background
        c.setFillColor(NAVY)
        c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

        # decorative band
        c.setFillColor(colors.HexColor("#193f61"))
        c.rect(0, PAGE_H * 0.478, PAGE_W, PAGE_H * 0.135, stroke=0, fill=1)

        # gold rules
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.1)
        c.line(28 * mm, PAGE_H - 46 * mm, PAGE_W - 28 * mm, PAGE_H - 46 * mm)
        c.line(28 * mm, 46 * mm, PAGE_W - 28 * mm, 46 * mm)

        # eyebrow
        c.setFillColor(GOLD)
        c.setFont("Body-Bold", 9.5)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 40 * mm,
                            "A  C O M P R E H E N S I V E   M A N U A L")

        # title
        c.setFillColor(colors.white)
        y = PAGE_H - 76 * mm
        for line, size in (("THE ULTIMATE GUIDE", 29), ("TO A", 18),
                           ("SUCCESSFUL MARRIAGE", 29)):
            c.setFont("Body-Bold", size)
            c.drawCentredString(PAGE_W / 2, y, line)
            y -= (size + 13)

        c.setFillColor(GOLD)
        c.setFont("Body-Bold", 13)
        c.drawCentredString(PAGE_W / 2, y - 10, "for Muslim Couples")

        # subtitle inside band
        c.setFillColor(colors.HexColor("#cfe2f3"))
        c.setFont("Body-Italic", 9.8)
        c.drawCentredString(
            PAGE_W / 2, PAGE_H * 0.567,
            "Synthesizing wisdom from 20 bestselling books on")
        c.drawCentredString(PAGE_W / 2, PAGE_H * 0.539,
                            "Islamic and modern relationship guidance")

        # ayah
        c.setFillColor(colors.HexColor("#e8eef4"))
        c.setFont("Body-Italic", 10)
        ayah = [
            "\u201cAnd among His signs is that He created for you from",
            "yourselves mates that you may find tranquility in them;",
            "and He placed between you affection and mercy.\u201d",
        ]
        y = PAGE_H * 0.415
        for line in ayah:
            c.drawCentredString(PAGE_W / 2, y, line)
            y -= 15
        c.setFillColor(GOLD)
        c.setFont("Body-Bold", 9.5)
        c.drawCentredString(PAGE_W / 2, y - 6, "Quran 30:21")

        # stats strip
        stats = [("5", "PARTS"), ("27", "CHAPTERS"),
                 ("22", "APPENDICES"), (str(m["pages"]), "PAGES")]
        n = len(stats)
        strip_y = PAGE_H * 0.285
        col = (PAGE_W - 56 * mm) / n
        for i, (num, label) in enumerate(stats):
            cx = 28 * mm + col * (i + 0.5)
            c.setFillColor(colors.white)
            c.setFont("Body-Bold", 21)
            c.drawCentredString(cx, strip_y, num)
            c.setFillColor(colors.HexColor("#9fc0d8"))
            c.setFont("Body", 7.6)
            c.drawCentredString(cx, strip_y - 13, label)
            if i:
                c.setStrokeColor(colors.HexColor("#2b5578"))
                c.setLineWidth(0.6)
                c.line(28 * mm + col * i, strip_y - 16,
                       28 * mm + col * i, strip_y + 20)

        # footer
        c.setFillColor(colors.HexColor("#9fc0d8"))
        c.setFont("Body", 9)
        c.drawCentredString(PAGE_W / 2, 34 * mm, m["edition"])
        c.setFont("Body", 8)
        c.drawCentredString(PAGE_W / 2, 27 * mm, m["date"])
        c.restoreState()


class PartDivider(Flowable):
    """Full-page divider announcing a new part."""

    def __init__(self, number, title, blurb=""):
        super().__init__()
        self.number, self.title, self.blurb = number, title, blurb

    def wrap(self, aw, ah):
        self._aw, self._ah = aw, ah
        return aw, ah

    def draw(self):
        c = self.canv
        doc = getattr(c, "_bookdoc", None)
        if doc is not None:
            doc.divider_pages.add(c.getPageNumber())
        c.saveState()
        x, y = c.absolutePosition(0, 0)
        c.translate(-x, -y)

        c.setFillColor(NAVY)
        c.rect(0, PAGE_H * 0.40, PAGE_W, PAGE_H * 0.26, stroke=0, fill=1)

        c.setStrokeColor(GOLD)
        c.setLineWidth(1)
        c.line(PAGE_W / 2 - 22 * mm, PAGE_H * 0.615,
               PAGE_W / 2 + 22 * mm, PAGE_H * 0.615)

        c.setFillColor(GOLD)
        c.setFont("Body-Bold", 11)
        c.drawCentredString(PAGE_W / 2, PAGE_H * 0.578, f"PART {self.number}")

        c.setFillColor(colors.white)
        words = self.title.upper().split()
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if len(trial) > 26:
                lines.append(cur)
                cur = w
            else:
                cur = trial
        lines.append(cur)
        y = PAGE_H * 0.518
        for line in lines:
            c.setFont("Body-Bold", 22)
            c.drawCentredString(PAGE_W / 2, y, line)
            y -= 28

        if self.blurb:
            c.setFillColor(colors.HexColor("#5a6b78"))
            c.setFont("Body-Italic", 10.5)
            c.drawCentredString(PAGE_W / 2, PAGE_H * 0.345, self.blurb)

        c.setStrokeColor(LIGHT)
        c.setLineWidth(0.8)
        c.line(PAGE_W / 2 - 30 * mm, PAGE_H * 0.305,
               PAGE_W / 2 + 30 * mm, PAGE_H * 0.305)
        c.restoreState()


PART_BLURBS = {
    "1": "Why marriage exists, and what it is for",
    "2": "The skills that make a marriage thrive",
    "3": "Money, family, children, work and health",
    "4": "Drift, betrayal, harm, trials and endings",
    "5": "What remains when the marriage is over",
}


# --------------------------------------------------------------------------
# Document template
# --------------------------------------------------------------------------
class BookDoc(BaseDocTemplate):
    def __init__(self, path, meta):
        super().__init__(
            path, pagesize=A4,
            leftMargin=21 * mm, rightMargin=21 * mm,
            topMargin=22 * mm, bottomMargin=20 * mm,
            title=meta["title"], author=meta["author"],
            subject="A Comprehensive Manual for Muslim Couples",
            creator="build_book.py",
        )
        self.meta = meta
        # page -> heading label, accumulated during each layout pass and
        # reused by the next one (multiBuild runs several passes)
        self.chapter_by_page: dict[int, str] = {}
        self.plain_pages: set[int] = set()    # no header/footer
        self.divider_pages: set[int] = set()  # full-page part dividers

        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="body")
        full = Frame(0, 0, PAGE_W, PAGE_H, id="full",
                     leftPadding=0, rightPadding=0,
                     topPadding=0, bottomPadding=0)
        # "plain" is first so that page 1 (the cover) carries no furniture
        self.addPageTemplates([
            PageTemplate(id="plain", frames=[full], onPage=self.blank),
            PageTemplate(id="main", frames=[frame], onPageEnd=self.decorate),
        ])

    # -- page furniture ----------------------------------------------------
    def blank(self, canvas, doc):
        canvas._bookdoc = self
        self.plain_pages.add(canvas.getPageNumber())

    def decorate(self, canvas, doc):
        canvas._bookdoc = self
        page = canvas.getPageNumber()
        if page in self.plain_pages or page in self.divider_pages:
            return
        canvas.saveState()
        canvas.setFont("Body", 7.4)
        canvas.setFillColor(MUTED)
        canvas.drawString(doc.leftMargin, PAGE_H - 14 * mm,
                          self.meta["short_title"])
        # the running head shows the most recent heading at or before this
        # page; front matter has none, so it stays blank there
        prior = [p for p in self.chapter_by_page if p <= page]
        if prior:
            label = self.chapter_by_page[max(prior)]
            canvas.drawRightString(PAGE_W - doc.rightMargin, PAGE_H - 14 * mm,
                                   label[:62])
        canvas.setStrokeColor(colors.HexColor("#dde3e8"))
        canvas.setLineWidth(0.4)
        canvas.line(doc.leftMargin, PAGE_H - 16 * mm,
                    PAGE_W - doc.rightMargin, PAGE_H - 16 * mm)
        canvas.line(doc.leftMargin, 14 * mm, PAGE_W - doc.rightMargin, 14 * mm)
        canvas.setFont("Body", 8.2)
        canvas.setFillColor(colors.HexColor("#5d6d7e"))
        canvas.drawCentredString(PAGE_W / 2, 9.5 * mm, str(page))
        canvas.restoreState()

    # -- TOC + bookmark wiring --------------------------------------------
    def afterFlowable(self, flowable):
        level = getattr(flowable, "_toc_level", None)
        if level is None:
            return
        label = flowable._toc_label
        key = f"h{level}-{self.page}-{abs(hash(label)) % 10**8}"
        self.canv.bookmarkPage(key)
        # multiBuild lays the document out several times with a fresh canvas
        # each pass, so the outline must be rebuilt per canvas, not once
        seen = getattr(self.canv, "_outline_keys", None)
        if seen is None:
            seen = self.canv._outline_keys = set()
        if key not in seen:
            seen.add(key)
            self.canv.addOutlineEntry(label, key, level=level, closed=(level == 0))
        self.notify("TOCEntry", (level, label, self.page, key))
        self.chapter_by_page[self.page] = label


# --------------------------------------------------------------------------
# Body assembly
# --------------------------------------------------------------------------
def front_matter(meta, S):
    """Cover, title page, copyright/disclaimer, how-to-use, TOC."""
    tiny = ParagraphStyle("tiny", parent=S["body"], fontSize=8.6, leading=12.4,
                          alignment=TA_JUSTIFY, textColor=colors.HexColor("#3d4f5c"))
    ctr = ParagraphStyle("ctr", parent=S["body"], alignment=TA_CENTER)
    ctrb = ParagraphStyle("ctrb", parent=ctr, fontName="Body-Bold")

    F = []

    # ---- cover (plain template; page 1 carries no header or number) ----
    F.append(CoverPage(meta))
    F.append(_NextMain())
    F.append(PageBreak())

    # ---- title page ----
    F.append(Spacer(1, 42 * mm))
    F.append(Paragraph("THE ULTIMATE GUIDE<br/>TO A SUCCESSFUL MARRIAGE",
                       ParagraphStyle("tp", parent=S["title"], fontSize=23,
                                      leading=30, textColor=NAVY)))
    F.append(Spacer(1, 5 * mm))
    F.append(HRFlowable(width="42%", thickness=1.1, color=GOLD, hAlign="CENTER"))
    F.append(Spacer(1, 6 * mm))
    F.append(Paragraph("A Comprehensive Manual for Muslim Couples", ctr))
    F.append(Paragraph(
        "<i>Synthesizing wisdom from twenty bestselling books on Islamic "
        "and modern relationship guidance</i>", ctr))
    F.append(Spacer(1, 30 * mm))
    F.append(Paragraph(meta["edition"], ctrb))
    F.append(Paragraph(meta["date"], ctr))
    F.append(Spacer(1, 8 * mm))
    F.append(Paragraph(
        f"{meta['pages']} pages &nbsp;·&nbsp; 27 chapters &nbsp;·&nbsp; "
        "22 appendices &nbsp;·&nbsp; 5 parts", ctr))
    F.append(PageBreak())

    # ---- sources + disclaimer ----
    F.append(Paragraph("Sources & Acknowledgments", S["h2"]))
    F.append(Paragraph(
        "This guide is a compilation and synthesis. All Islamic material is "
        "drawn from the Quran and the established hadith collections; all "
        "psychological material is attributed in-text to its author. Nothing "
        "here replaces the primary sources — it points you toward them.", tiny))
    F.append(Spacer(1, 3 * mm))
    F.append(Paragraph("Islamic sources", S["h4"]))
    F.append(Paragraph(
        "The Holy Quran &nbsp;· Sahih al-Bukhari &amp; Sahih Muslim &nbsp;· "
        "<i>The Muslim Marriage Guide</i> (Ruqaiyyah Waris Maqsood) &nbsp;· "
        "<i>A Gift for Nikah</i> (Abdul Raheem Limbada) &nbsp;· "
        "<i>The Essentials of Islamic Marriage</i> (Muhammad Rifat Uthman) &nbsp;· "
        "<i>Handbook of a Healthy Muslim Marriage</i> (Abdur-Rahman ibn Yusuf "
        "Mangera) &nbsp;· <i>Before You Tie the Knot</i> (Salma Abugideiri &amp; "
        "Mohamed Hag Magid) &nbsp;· <i>Dwell in Tranquility</i> (Kamal Shaarawy) "
        "&nbsp;· <i>With the Heart in Mind</i> (Mikaeel Ahmed Smith) &nbsp;· "
        "<i>The Marriage Guide According to the Sunnah</i> (Imam al-Albani)", tiny))
    F.append(Spacer(1, 2 * mm))
    F.append(Paragraph("General relationship sources", S["h4"]))
    F.append(Paragraph(
        "<i>The 5 Love Languages</i> (Gary Chapman) &nbsp;· "
        "<i>The Seven Principles for Making Marriage Work</i> and "
        "<i>The Relationship Cure</i> (John Gottman) &nbsp;· "
        "<i>Men Are from Mars, Women Are from Venus</i> (John Gray) &nbsp;· "
        "<i>Hold Me Tight</i> (Sue Johnson) &nbsp;· "
        "<i>Attached</i> (Amir Levine &amp; Rachel Heller) &nbsp;· "
        "<i>Love &amp; Respect</i> (Emerson Eggerichs) &nbsp;· "
        "<i>Mating in Captivity</i> (Esther Perel) &nbsp;· "
        "<i>Nonviolent Communication</i> (Marshall Rosenberg) &nbsp;· "
        "<i>The Mastery of Love</i> (Don Miguel Ruiz)", tiny))

    F.append(Spacer(1, 6 * mm))
    F.append(Paragraph("Important Disclaimers", S["h2"]))
    for head, txt in [
        ("Educational, not a fatwa.",
         "Rulings on divorce, inheritance, custody, polygyny and medical "
         "treatment vary between schools of thought and between countries. "
         "Consult a qualified scholar for any ruling that affects you."),
        ("Legal matters require a lawyer.",
         "This is especially true of wills (Chapter 26) and second marriages "
         "(Chapter 25). An Islamic instrument alone is not legally binding in "
         "most jurisdictions, including India, the UK, the US and Canada."),
        ("Not therapy.",
         "Chapters 17 to 20 address betrayal trauma, addiction, depression and "
         "abuse. Please involve a licensed professional. Seeking treatment is "
         "prophetic practice, not weakness."),
        ("Safety comes before patience.",
         "If you are being physically harmed or threatened, your priority is "
         "safety. Islam does not require you to remain in danger. See Chapter 18 "
         "and Appendix M, and contact local authorities or a domestic violence "
         "helpline."),
    ]:
        F.append(Paragraph(f"<b>{head}</b> {txt}", tiny))
    F.append(Spacer(1, 6 * mm))
    F.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#cfd8dc")))
    F.append(Spacer(1, 3 * mm))
    F.append(Paragraph(
        f"<font size=8 color='#7a8b99'>{meta['edition']} · {meta['date']}. "
        "Compiled from Islamic and modern relationship expertise. "
        "Distributed freely for the benefit of Muslim couples — "
        "please share it, and make du'a for everyone who worked on it.</font>",
        ctr))
    F.append(PageBreak())

    # ---- how to use ----
    F.append(Paragraph("How to Use This Guide", S["h1"]))
    F.append(Paragraph(
        f"This is a reference manual, not a novel. You are not expected to read "
        f"{meta['pages']} pages in order, and you will get more from it if you "
        f"don't try.", S["body"]))
    F.append(Spacer(1, 2 * mm))
    for head, txt in [
        ("If your marriage is new",
         "Start with Parts 1 and 2 (Chapters 1–10). Do the exercises together "
         "rather than reading silently. Then read Part 5, Chapter 22, early — "
         "deciding what your household is <i>for</i> is much easier before "
         "habits set."),
        ("If your marriage is settled and busy",
         "Go to Chapter 16 (drift), then Appendix K and run one weekly "
         "\u201cState of the Union\u201d meeting. That single habit outperforms "
         "everything else in this book."),
        ("If your marriage is in crisis",
         "Turn to Appendix P, the Crisis Decision Tree. It will route you to "
         "the right chapter in under a minute. If there is any fear or harm "
         "involved, go to Appendix M first."),
        ("If you are considering or recovering from divorce",
         "Chapter 21 covers the Islamic framework and the steps most couples "
         "skip. Chapter 25 covers what comes after."),
        ("If you are planning for the long term",
         "Part 5. Chapter 26 in particular contains the two things almost "
         "nobody does and everybody should: a valid will, and the letters."),
    ]:
        F.append(Paragraph(f"<b>{head}.</b> {txt}", S["body"]))

    F.append(Spacer(1, 3 * mm))
    F.append(Paragraph("Three ways to get more from it", S["h3"]))
    for txt in [
        "<b>Read it together.</b> Almost every chapter ends with reflection "
        "questions designed to be answered aloud, by both spouses.",
        "<b>Do one thing.</b> A single exercise actually practised beats five "
        "chapters merely admired. Pick one per week.",
        "<b>Come back to it.</b> The chapter that seems irrelevant today is "
        "the one you will need in five years. Keep it where you can find it.",
    ]:
        F.append(Paragraph(txt, S["li"], bulletText="\u2022"))

    F.append(Spacer(1, 5 * mm))
    F.append(Paragraph(
        "<i>\u201cThe most beloved deeds to Allah are those done consistently, "
        "even if they are few.\u201d</i> \u2014 <b>Bukhari, Muslim</b>", S["quote"]))
    F.append(PageBreak())

    # ---- table of contents ----
    F.append(Paragraph("Table of Contents", S["h1"]))
    F.append(Spacer(1, 3 * mm))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("toc0", fontName="Body-Bold", fontSize=10.6, leading=19,
                       textColor=NAVY, spaceBefore=9, spaceAfter=1,
                       leftIndent=0, firstLineIndent=0),
        ParagraphStyle("toc1", fontName="Body", fontSize=9.3, leading=14.4,
                       textColor=colors.HexColor("#2c3e50"),
                       leftIndent=13, firstLineIndent=-1),
    ]
    toc.dotsMinLevel = 0
    F.append(toc)
    F.append(PageBreak())
    return F


def body_flowables(md_text, S, avail_width):
    """Convert markdown, tagging headings for TOC/bookmarks and inserting
    part dividers and chapter page breaks."""
    out = []
    lines = md_text.split("\n")
    # strip the source's own front matter: start at the first PART heading
    start = 0
    for i, l in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)$", l.strip())
        if m and classify(m.group(2), len(m.group(1)))[0] == 0:
            start = i
            break
    lines = lines[start:]

    # split into segments at part/chapter/appendix headings
    segments, buf = [], []
    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
        if m:
            level, label = classify(m.group(2), len(m.group(1)))
            if level is not None:
                if buf:
                    segments.append(("body", "\n".join(buf)))
                    buf = []
                segments.append(("head", (level, label, m.group(2))))
                continue
        buf.append(line)
    if buf:
        segments.append(("body", "\n".join(buf)))

    first_part = True
    fresh_page = False   # True when a divider has just started a new page
    for kind, payload in segments:
        if kind == "body":
            chunk = bd.md_to_flowables(payload, S, avail_width)
            if fresh_page:
                # drop leading decoration (rules/spacers) that would otherwise
                # occupy the page immediately after a part divider
                while chunk and isinstance(chunk[0], (HRFlowable, Spacer)):
                    chunk.pop(0)
            if chunk:
                fresh_page = False
            out.extend(chunk)
            continue

        level, label, raw = payload
        if level == 0:
            num = RE_PART.match(
                bd.clean_for_pdf(re.sub(r"[*_`]", "", raw)).strip()).group(1)
            title = label.split(":", 1)[1].strip()
            if not first_part:
                out.append(PageBreak())
            first_part = False
            out.append(_NextPlain())
            # invisible anchor sits on the divider page itself, so the TOC
            # entry and the bookmark both point at the divider
            p = Paragraph(f'<font color="#ffffff" size="1">{label}</font>',
                          S["body"])
            p._toc_level, p._toc_label = 0, label
            p._divider_anchor = True
            out.append(p)
            # the divider consumes the whole frame, so the next flowable
            # already starts a fresh page — no explicit PageBreak needed
            out.append(PartDivider(num, title, PART_BLURBS.get(num, "")))
            out.append(_NextMain())
            fresh_page = True
        else:
            if not fresh_page:
                out.append(PageBreak())
            fresh_page = False
            p = Paragraph(bd.inline_md_to_rl(raw), S["h1"])
            p._toc_level, p._toc_label = 1, label
            out.append(p)
            out.append(HRFlowable(width="100%", thickness=1.1, color=LIGHT,
                                  spaceBefore=2, spaceAfter=7))
    return out


class _NextPlain(Flowable):
    """Switch the following page to the borderless full-page template."""
    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        pass

    def __init__(self):
        super().__init__()
        self._tmpl = "plain"


class _NextMain(_NextPlain):
    def __init__(self):
        super().__init__()
        self._tmpl = "main"


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------
def _render(src: str, dst: str, meta: dict) -> int:
    bd.register_fonts()
    S = bd.build_styles()
    md_text = open(src, encoding="utf-8").read()

    doc = BookDoc(dst, meta)
    story = front_matter(meta, S) + body_flowables(md_text, S, doc.width)

    # honour the template-switch markers
    from reportlab.platypus import NextPageTemplate
    expanded = []
    for f in story:
        if isinstance(f, _NextPlain):
            expanded.append(NextPageTemplate(f._tmpl))
        else:
            expanded.append(f)

    doc.multiBuild(expanded)

    import pypdfium2 as pdfium
    return len(pdfium.PdfDocument(dst))


def build(src: str, dst: str) -> int:
    meta = {
        "title": "The Ultimate Guide to a Successful Marriage",
        "short_title": "THE ULTIMATE GUIDE TO A SUCCESSFUL MARRIAGE",
        "author": "Compiled from Islamic & Modern Relationship Expertise",
        "edition": "Final Edition \u00b7 Version 3.0 \u00b7 Parts 1\u20135 Complete",
        "date": "15 August 2026",
        "pages": "230",
    }

    # first pass establishes the real page count, second bakes it into the
    # cover and title page so the advertised length is always accurate
    n = _render(src, dst, meta)
    if str(n) != meta["pages"]:
        meta["pages"] = str(n)
        n = _render(src, dst, meta)

    print(f"  {dst}  —  {n} pages, {os.path.getsize(dst)//1024} KB")
    return n


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    build(sys.argv[1], sys.argv[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
