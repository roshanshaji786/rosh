# Project Summary

**THE ULTIMATE GUIDE TO A SUCCESSFUL MARRIAGE**
A Comprehensive Manual for Muslim Couples

**Version:** 2.0 (Parts 1–4 Complete)
**Date:** August 15, 2026
**Repository:** https://github.com/roshanshaji786/rosh

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| **Total pages (PDF)** | **192** |
| Total parts | 4 of 5 |
| Total chapters | 21 |
| Total appendices | 16 (A–P) |
| Markdown lines | ~8,100 |
| Islamic sources | 10 books + Quran & the two Sahihs |
| General relationship sources | 10 books |
| Practical exercises | 60+ |
| Worksheets & templates | 16 |
| Duas included | 25+ |

---

## 📕 Deliverables

### Primary
- **`ULTIMATE_MARRIAGE_GUIDE_COMPLETE_Parts_1-4.pdf`** — 192 pages, A4, paginated, running headers
- `ULTIMATE_MARRIAGE_GUIDE_COMPLETE_Parts_1-4.html` — browser edition
- `ULTIMATE_MARRIAGE_GUIDE_COMPLETE_Parts_1-4.md` — source

### Individual parts
- `ULTIMATE_MARRIAGE_GUIDE_Parts_1-3.{md,html,pdf}` — 145 pages, Ch. 1–15, App. A–J
- `ULTIMATE_MARRIAGE_GUIDE_Part_4.{md,html,pdf}` — 47 pages, Ch. 16–21, App. K–P

### Supporting
- `tools/build_docs.py` — pure-Python markdown → HTML + PDF builder
- `README.md` — documentation
- `CONVERSION_GUIDE.md` — build instructions & troubleshooting

---

## ✅ Part 4: Overcoming Challenges (New in v2.0)

| Ch. | Title | Core content |
|-----|-------|--------------|
| 16 | When Love Fades | Mawaddah vs. rahmah, bids for connection (Gottman 86% vs. 33%), Perel's closeness/desire paradox, Negative Sentiment Override & *husn al-dhann*, love-map rebuild, the Magic Six Hours, rekindling through worship, asymmetric motivation |
| 17 | Trust & Betrayal | Six forms of betrayal, *mithaqan ghaliza*, betrayal trauma, the seven conditions of recovery, the four conditions of tawbah incl. *haqq al-'ibad*, Atone → Attune → Attach, pornography (spiritual + neurological), the trust ledger, forgiveness vs. trust |
| 18 | Anger, Harm & Toxic Patterns | Prophetic anger protocol, diffuse physiological arousal & the 20-minute rule, time-out agreement, Four Horsemen antidotes, contempt as top divorce predictor, seven toxic patterns, the six-level Escalation Ladder, abuse defined, the unambiguous Islamic position (incl. a careful treatment of 4:34), guidance for families & imams, and for those causing harm |
| 19 | Trials | Infertility (Quran 42:49–50, IVF & kafalah notes, the Shield Agreement), miscarriage & child loss, chronic illness & caregiver burnout, mental illness & stigma, financial catastrophe, the Trial Protocol, the duas of the Prophets |
| 20 | Modern Pressures | Phubbing research, the Household Tech Charter, the comparison trap, the Screenshot Test, long-distance marriage (incl. Umar RA's four-month standard), addiction (the four C's, non-shaming approach), deen vs. 'urf vs. preference, burnout & the second shift |
| 21 | Divorce & Reconciliation | "Most hated of permissible things" read precisely, the seven-step Quranic pre-divorce process incl. the commanded 4:35 arbitration, indicators divorce may be right, talaq/khula/faskh/mubara'ah/tafwid, talaq al-Sunnah, talaq in anger, the ethics of divorcing well, children as non-parties, the reconciliation off-ramps, life after divorce & dismantling stigma |

### Appendices K–P
- **K** — Weekly "State of the Union" meeting agenda + score sheet
- **L** — Transparency & Trust-Rebuilding Agreement (7 sections, incl. sunset clause)
- **M** — Safety Assessment checklist & Safety Plan (documents, contacts, digital safety)
- **N** — Duas for Hardship & Healing (Yunus, Ayyub, Zakariyya, istikhara, and more)
- **O** — Household Tech Charter template (12 commitments)
- **P** — Crisis Decision Tree (safety → betrayal → trial → toxicity → drift)

---

## 🔧 PDF Generation — Resolved

Earlier versions of this project shipped without a PDF because pandoc, wkhtmltopdf, and WeasyPrint's system libraries were unavailable in the build environment.

**This is now fixed.** `tools/build_docs.py` generates the PDF using only `markdown` + `reportlab` + `fonttools` — all pip-installable, with no system library dependencies. It handles headings, tables (with repeating headers), blockquotes, nested lists, fenced code, pagination, running headers, page numbers, glyph coverage filtering, and auto-repair of malformed inline markup.

```bash
pip install --break-system-packages markdown reportlab fonttools
python3 tools/build_docs.py --all
```

---

## 🗺️ Remaining Work

**Part 5: Creating a Lasting Legacy** (~20 pages)
- Growing old together — marriage in the later decades
- Raising righteous children and grandchildren
- Remarriage, blended families & second chances
- Marriage as sadaqah jariyah
- Reuniting in Jannah

---

## ⚠️ Disclaimers

- **Educational, not a fatwa.** Consult a qualified scholar for rulings; consult a lawyer for legal matters.
- **Not therapy.** Chapters 17–20 address trauma, addiction, depression, and abuse — involve licensed professionals.
- **Safety over patience.** See Chapter 18 and Appendix M.
