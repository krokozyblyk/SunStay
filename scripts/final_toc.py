"""Copy the exact static TOC layout from the previous course PZ into the
SunStay PZ. Title page and appendices are left untouched."""
from pathlib import Path
import glob

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph

OLD = Path(glob.glob(r"C:\Users\Redmibook\Desktop\Zadanie_tz\**\Пояснительная записка.docx", recursive=True)[0])
DOCS = Path(__file__).resolve().parents[1] / "docs"
FILES = ["Пояснительная_записка_SunStay.docx", "Пояснительная_записка_без_титульника.docx"]

NEEDLE = "СОДЕРЖАНИЕ"


def text_of(p):
    return p.text.strip()


def collect_old_toc():
    d = Document(str(OLD))
    items = []
    started = False
    for p in d.paragraphs:
        t = text_of(p)
        if t == NEEDLE:
            started = True
            continue
        if started and p.style.name.startswith("toc"):
            items.append((t, p.style.name))
        elif started and items and t:
            break
    return items


def add_para(anchor, text, style_name=None):
    el = OxmlElement("w:p")
    anchor._p.addnext(el)
    para = Paragraph(el, anchor._parent)
    if style_name:
        try:
            para.style = style_name
        except KeyError:
            pass
    run = para.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0, 0, 0)
    run.font.underline = False
    para.paragraph_format.first_line_indent = Pt(0)
    return para


def process(name, old_items):
    path = DOCS / name
    doc = Document(str(path))
    paras = list(doc.paragraphs)

    toc_idx = next((i for i, p in enumerate(paras) if text_of(p) == NEEDLE), None)
    intro_idx = next((i for i, p in enumerate(paras)
                      if text_of(p).startswith("ВВЕДЕНИЕ")
                      and (p.style.name.endswith("11") or p.style.name.startswith("Heading"))
                      and toc_idx is not None and i > toc_idx), None)
    if toc_idx is None or intro_idx is None:
        print("SKIP", name)
        return

    # delete existing TOC entries (the field result)
    for p in paras[toc_idx + 1:intro_idx]:
        if p.style.name.startswith("toc"):
            p._element.getparent().remove(p._element)

    # rebuild from the example, plus appendices at the end
    anchor = paras[toc_idx]
    for text, style in old_items:
        if text.startswith("Приложение"):
            continue
        anchor = add_para(anchor, text, style)
    for line in [
        "Приложение А. Техническое задание\t1",
        "Приложение Б. Текст программы\t1",
        "Приложение В. Сценарий и результаты тестовых испытаний\t1",
        "Приложение Г. Руководство пользователя\t1",
        "Приложение Д. Скрипт базы данных\t1",
    ]:
        anchor = add_para(anchor, line, "toc 1")

    # remove standalone word ПРИЛОЖЕНИЯ from body
    for p in list(doc.paragraphs):
        if text_of(p) == "ПРИЛОЖЕНИЯ":
            p._element.getparent().remove(p._element)

    # center all СОДЕРЖАНИЕ headings, make every TOC line black
    for p in doc.paragraphs:
        if text_of(p) == NEEDLE:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if p.style.name.startswith("toc") or p.style.name.startswith("Оглавление"):
            for run in p.runs:
                run.font.color.rgb = RGBColor(0, 0, 0)
                run.font.underline = False

    doc.save(str(path))
    print("DONE", name)


if __name__ == "__main__":
    items = collect_old_toc()
    print("OLD TOC ITEMS", len(items), items[:3], items[-3:])
    for f in FILES:
        process(f, items)
