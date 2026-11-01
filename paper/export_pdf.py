"""Render the title and abstract in main.tex as a one-page PDF."""

from pathlib import Path
import re

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


source = Path(__file__).with_name("main.tex").read_text(encoding="utf-8")
title = re.search(r"\\bfseries (.*?)\\par", source).group(1)
abstract = re.search(
    r"\\begin\{abstract\}\s*(.*?)\s*\\end\{abstract\}", source, re.DOTALL
).group(1)
abstract = " ".join(abstract.split())

destination = Path(__file__).resolve().parents[1] / "output" / "pdf"
destination.mkdir(parents=True, exist_ok=True)
pdf_path = destination / "sorting_pick_title_abstract.pdf"

document = SimpleDocTemplate(
    str(pdf_path),
    pagesize=A4,
    leftMargin=28 * mm,
    rightMargin=28 * mm,
    topMargin=30 * mm,
    bottomMargin=28 * mm,
    title=title,
)
title_style = ParagraphStyle(
    "Title", fontName="Times-Bold", fontSize=16, leading=19, alignment=TA_CENTER
)
heading_style = ParagraphStyle(
    "Abstract heading",
    fontName="Times-Bold",
    fontSize=11,
    leading=14,
    alignment=TA_CENTER,
)
body_style = ParagraphStyle(
    "Abstract body",
    fontName="Times-Roman",
    fontSize=11,
    leading=15,
    alignment=TA_JUSTIFY,
    leftIndent=9 * mm,
    rightIndent=9 * mm,
    spaceBefore=7 * mm,
)
document.build(
    [
        Paragraph(title, title_style),
        Spacer(1, 14 * mm),
        Paragraph("Abstract", heading_style),
        Paragraph(abstract, body_style),
    ]
)
print(f"{pdf_path} ({len(abstract.split())} abstract words)")
