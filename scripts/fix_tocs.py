"""Adjust TOCs of the SunStay PZ to match the previous course style.
Title page is never modified."""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph

DOCS = Path(__file__).resolve().parents[1] / "docs"
FILES = ["Пояснительная_записка_SunStay.docx", "Пояснительная_записка_без_титульника.docx"]

APPENDIX_LINES = [
    "Приложение А. Техническое задание\t1",
    "Приложение Б. Текст программы\t1",
    "Приложение В. Сценарий и результаты тестовых испытаний\t1",
    "Приложение Г. Руководство пользователя\t1",
    "Приложение Д. Скрипт базы данных\t1",
]


def text_of(p):
    return p.text.strip()


def plain_black(para):
    for run in para.runs:
        run.font.color.rgb = RGBColor(0, 0, 0)
        run.font.underline = False


def add_after(anchor, text):
    el = OxmlElement("w:p")
    anchor._p.addnext(el)
    para = Paragraph(el, anchor._parent)
    run = para.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 0)
    para.paragraph_format.first_line_indent = Pt(0)
    return para


def process(name):
    path = DOCS / name
    doc = Document(str(path))
    paras = list(doc.paragraphs)

    # main contents heading — centered
    toc_headings = [p for p in paras if text_of(p) == "СОДЕРЖАНИЕ"]
    if toc_headings:
        toc_headings[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # main TOC: keep normal sections; replace everything from ПРИЛОЖЕНИЯ
    # with five appendix lines at the end (as in the previous course project)
    start = next((i for i, p in enumerate(paras) if text_of(p) == "СОДЕРЖАНИЕ"), None)
    intro = next((i for i, p in enumerate(paras)
                  if text_of(p).startswith("ВВЕДЕНИЕ") and p.style.name.endswith("11")), None)
    if start is not None and intro is not None and intro > start:
        entries = [p for p in paras[start + 1:intro] if p.style.name.startswith("toc")]
        cut = next((i for i, p in enumerate(entries)
                    if text_of(p).startswith("ПРИЛОЖЕНИЯ")), len(entries))
        for p in entries[cut:]:
            p._element.getparent().remove(p._element)
        for p in entries[:cut]:
            plain_black(p)
        anchor = entries[cut - 1] if cut else paras[start]
        for line in APPENDIX_LINES:
            anchor = add_after(anchor, line)

    # remove the standalone word ПРИЛОЖЕНИЯ from the body
    for p in list(doc.paragraphs):
        if text_of(p) == "ПРИЛОЖЕНИЯ":
            p._element.getparent().remove(p._element)

    # appendix contents headings centered, all TOC text black
    for p in doc.paragraphs:
        if text_of(p) == "СОДЕРЖАНИЕ":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if p.style.name.startswith("toc"):
            plain_black(p)

    doc.save(str(path))
    print("FIXED", name)


for f in FILES:
    process(f)
