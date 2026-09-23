"""Render the complete technical Markdown report as a visually checked PDF."""

import html
import re
import shutil
from pathlib import Path

from build_architecture import architecture
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/AEGIS-submission-report.pdf"
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="BodyReport", fontName="Helvetica", fontSize=9, leading=12, spaceAfter=7))
styles.add(ParagraphStyle(name="CellReport", fontName="Helvetica", fontSize=6.8, leading=9, wordWrap="CJK"))
styles.add(ParagraphStyle(name="CodeReport", fontName="Courier", fontSize=7, leading=10, wordWrap="CJK", spaceAfter=5))
for n in ["Title", "Heading1", "Heading2", "Heading3"]:
    styles[n].textColor = colors.HexColor("#173f39")
styles["Heading1"].fontSize = 15
styles["Heading1"].leading = 19
styles["Heading1"].spaceBefore = 14


def inline(s):
    for a, b in {
        "—": " - ",
        "–": "-",
        "→": "->",
        "≈": "~",
        "≥": ">=",
        "÷": "/",
        "≤": "<=",
        "’": "'",
        "“": '"',
        "”": '"',
        "×": "x",
    }.items():
        s = s.replace(a, b)
    s = html.escape(s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', s)
    return s


lines = (ROOT / "docs/technical-report.md").read_text(encoding="utf-8").splitlines()
story = []
i = 0
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    if line.startswith("```"):
        i += 1
        while i < len(lines) and not lines[i].startswith("```"):
            story.append(Paragraph(html.escape(lines[i]), styles["CodeReport"]))
            i += 1
        i += 1
        continue
    if line.startswith("!["):
        d = architecture()
        d.scale(505 / 720, 505 / 720)
        d.width = 505
        d.height = 420 * 505 / 720
        story.extend([d, Spacer(1, 8)])
        i += 1
        continue
    if line.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            cells = [v.strip() for v in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r"[-: ]+", v) for v in cells):
                rows.append(cells)
            i += 1
        n = len(rows[0])
        widths = ([75] + [430 / (n - 1)] * (n - 1)) if n > 8 else ([165, 340] if n == 2 else [505 / n] * n)
        t = Table(
            [[Paragraph(inline(v), styles["CellReport"]) for v in row] for row in rows],
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT",
        )
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#deece6")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#173f39")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.extend([t, Spacer(1, 9)])
        continue
    if line == "## 4. Method":
        story.append(PageBreak())
    if line.startswith("#"):
        depth = len(line) - len(line.lstrip("#"))
        style = "Title" if depth == 1 else "Heading" + str(min(depth - 1, 3))
        story.append(Paragraph(inline(line.lstrip("#").strip()), styles[style]))
        i += 1
        continue
    parts = [line]
    i += 1
    while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "```", "![")):
        parts.append(lines[i].strip())
        i += 1
    story.append(Paragraph(inline(" ".join(parts)), styles["BodyReport"]))


def footer(canvas, doc):
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#173f39"))
    canvas.drawString(45, 25, "AEGIS | SENTINEL | Final report | 23 September 2026")
    canvas.drawRightString(550, 25, str(doc.page))


OUT.parent.mkdir(parents=True, exist_ok=True)
SimpleDocTemplate(
    str(OUT),
    pagesize=(595, 842),
    leftMargin=45,
    rightMargin=45,
    topMargin=40,
    bottomMargin=48,
    title="AEGIS - SENTINEL final technical report",
    author="Mourad Kraiem; Mohamed Yassin ghaoui; Amine Fathallah",
).build(story, onFirstPage=footer, onLaterPages=footer)
shutil.copy2(OUT, ROOT / "docs/AEGIS-submission-report.pdf")
print(OUT)
