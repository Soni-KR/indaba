"""Code-native architecture figure, matching implemented boundaries."""

from pathlib import Path

from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors

ROOT = Path(__file__).resolve().parents[1]


def architecture():
    d = Drawing(720, 420)
    navy = colors.HexColor("#173f39")

    def label(x, y, s, size=12):
        d.add(String(x, y, s, fontName="Helvetica", fontSize=size, fillColor=navy))

    def box(x, y, w, h, title, lines):
        d.add(Rect(x, y, w, h, rx=8, ry=8, fillColor=colors.HexColor("#eef6f3"), strokeColor=navy))
        label(x + 12, y + h - 23, title, 14)
        for i, line in enumerate(lines):
            label(x + 12, y + h - 46 - i * 18, line, 11)

    def arrow(x, y, end):
        d.add(Line(x, y, end, y, strokeColor=navy, strokeWidth=2))
        d.add(Polygon([end, y, end - 7, y + 4, end - 7, y - 4], fillColor=navy, strokeColor=navy))

    label(15, 395, "AEGIS: enforcement between proposed action and effect", 19)
    box(
        10,
        250,
        190,
        110,
        "Reference agent",
        ["Official mock / Qwen3-8B", "Unchanged prompt and tools", "Goal, retrieval, memory, history"],
    )
    box(
        230,
        170,
        270,
        190,
        "AEGIS action boundary",
        [
            "Permission and public schema",
            "Source-derived representations",
            "Persistent per-session evidence",
            "Streams within each destination",
            "Exact approvals and lifecycle",
            "Rewrite revalidation / final output",
        ],
    )
    box(
        530,
        250,
        180,
        110,
        "Decision -> simulator",
        ["ALLOW / BLOCK", "REWRITE / ESCALATE", "Simulated tools and response"],
    )
    arrow(200, 302, 228)
    arrow(500, 302, 528)
    box(
        10,
        60,
        190,
        120,
        "Trusted inputs",
        [
            "Policy and provenance",
            "Approval and result envelopes",
            "No scenario IDs, grading labels",
            "or reference plans in defense",
        ],
    )
    arrow(200, 145, 228)
    box(
        230,
        40,
        480,
        100,
        "Audit and dashboard",
        [
            "Source -> sensitive item -> candidate -> reason -> decision -> outcome",
            "Redacted hash-chain receipts; separately retained chain heads",
            "Known gap: no protection against cross-recipient collusion",
        ],
    )
    d.add(Line(365, 170, 365, 140, strokeColor=navy, strokeWidth=2))
    label(15, 15, "No learned defense model. No production authentication or distributed state guarantee.", 11)
    return d


if __name__ == "__main__":
    (ROOT / "output/pdf").mkdir(parents=True, exist_ok=True)
    renderSVG.drawToFile(architecture(), str(ROOT / "docs/architecture-final.svg"))
    renderPDF.drawToFile(architecture(), str(ROOT / "output/pdf/architecture-final.pdf"))
