"""Create two dedicated TOC styles and apply them. Nothing else is changed."""
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

DOCS = Path(__file__).resolve().parents[1] / "docs"
FILES = ["Пояснительная_записка_SunStay.docx", "Пояснительная_записка_без_титульника.docx"]
MAIN_STYLE = "Содержание"
APP_STYLE = "Содержание приложения"


def ensure_style(doc, name):
    try:
        style = doc.styles[name]
    except KeyError:
        style = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style.font.name = "Times New Roman"
    style.font.size = Pt(14)
    style.font.bold = False
    style.font.italic = False
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.first_line_indent = Cm(0)
    style.paragraph_format.left_indent = Cm(0)
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.line_spacing = 1.0
    style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    try:
        style.paragraph_format.tab_stops.add_tab_stop(
            Cm(16.0), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
        )
    except Exception:
        pass
    return style


def process(name):
    doc = Document(str(DOCS / name))
    ensure_style(doc, MAIN_STYLE)
    ensure_style(doc, APP_STYLE)

    paras = list(doc.paragraphs)
    toc_head_text = "СОДЕРЖАНИЕ"
    heads = [i for i, p in enumerate(paras) if p.text.strip() == toc_head_text]
    intro = next((i for i, p in enumerate(paras)
                  if p.text.strip().startswith("ВВЕДЕНИЕ")
                  and (p.style.name.endswith("11") or p.style.name.startswith("Heading"))
                  and heads and i > heads[0]), None)

    for i, p in enumerate(paras):
        is_toc = p.style.name.startswith(("toc", "Оглавление"))
        if not is_toc:
            continue
        if intro is not None and heads and heads[0] < i < intro:
            p.style = MAIN_STYLE
        else:
            p.style = APP_STYLE
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(14)
            r.font.color.rgb = RGBColor(0, 0, 0)
            r.font.underline = False

    doc.save(str(DOCS / name))
    print("STYLED", name)


for f in FILES:
    process(f)
