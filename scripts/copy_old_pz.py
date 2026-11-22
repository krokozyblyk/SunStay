"""Copy the previous course-project PZ verbatim, only adapting the topic to
SunStay and removing Appendix A (Technical assignment)."""
from __future__ import annotations

import copy
import glob
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml.ns import qn

OLD = Path(r"C:\Users\Redmibook\Desktop\Zadanie_tz")
OLD_PZ = Path(glob.glob(str(OLD / "**" / "Пояснительная записка.docx"), recursive=True)[0])
OLD_TITLE_CANDIDATES = list(OLD.glob("*Титульный лист*.docx"))
OLD_TITLE = OLD_TITLE_CANDIDATES[0] if OLD_TITLE_CANDIDATES else Path(
    r"C:\Users\Redmibook\Downloads\Титульный лист КП МДК 11.01 ТРЗБД 2023.docx")

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT_FULL = DOCS / "Пояснительная_записка_SunStay.docx"
OUT_NOTITLE = DOCS / "Пояснительная_записка_без_титульника.docx"

REPL = [
    ("Prizma", "SunStay"),
    ("PRIZMA", "SUNSTAY"),
    ("сети зоомагазинов", "гостиницы"),
    ("сеть зоомагазинов", "гостиницу"),
    ("зоомагазинов", "отелей"),
    ("зоомагазина", "отеля"),
    ("зоомагазин", "отель"),
    ("зоомагазины", "отели"),
    ("товаров, животных и услуг", "номеров, тарифов и услуг"),
    ("товары, животные и услуги", "номера, тарифы и услуги"),
    ("товаров и животных", "номеров и тарифов"),
    ("товары и животные", "номера и тарифы"),
    ("животных", "гостей"),
    ("животные", "гости"),
    ("животного", "гостя"),
    ("продуктов", "номеров"),
    ("продукты", "номера"),
    ("покупателей", "гостей"),
    ("покупателя", "гостя"),
    ("покупатель", "гость"),
    ("корзину", "бронирование"),
    ("корзина", "бронирование"),
    ("корзины", "бронирования"),
    ("заказов", "бронирований"),
    ("заказа", "брони"),
    ("заказ", "бронь"),
    ("акций", "акций и бонусов"),
    ("мобильное приложение", "веб-приложение"),
    ("мобильного приложения", "веб-приложения"),
    ("мобильному приложению", "веб-приложению"),
    ("React Native 0.85.3", "React 18 + TypeScript"),
    ("Node.js", "Python 3.13"),
    ("Express 5.x", "FastAPI"),
    ("PostgreSQL 18", "PostgreSQL 16"),
]


def replace_text(text: str) -> str:
    for a, b in REPL:
        text = text.replace(a, b).replace(a.capitalize(), b.capitalize())
    return text


def replace_in_doc(doc: Document) -> None:
    for para in doc.paragraphs:
        for run in para.runs:
            if run.text:
                run.text = replace_text(run.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        if run.text:
                            run.text = replace_text(run.text)


def copy_body_elements(src: Document, dst: Document, start=0, end=None) -> None:
    elements = list(src.element.body)
    for el in elements[start:end]:
        if el.tag in (qn("w:sectPr"),):
            continue
        dst.element.body.insert(len(dst.element.body) - 1, copy.deepcopy(el))


def remove_paragraphs_with(doc: Document, needles: list[str]) -> None:
    for para in list(doc.paragraphs):
        if any(n.lower() in para.text.lower() for n in needles):
            para._element.getparent().remove(para._element)


def main():
    doc = Document(str(OLD_PZ))
    title = Document(str(OLD_TITLE))

    # Save sectPr from original, we will reinsert at end
    sect = doc.element.body.find(qn("w:sectPr"))
    sect_copy = copy.deepcopy(sect) if sect is not None else None
    if sect is not None:
        doc.element.body.remove(sect)

    # Title page first (verbatim from the old project's title file, original order)
    title_elements = [copy.deepcopy(el) for el in title.element.body if el.tag != qn("w:sectPr")]
    for pos, el in enumerate(title_elements):
        doc.element.body.insert(pos, el)

    # Page break between title and contents
    pb = doc.add_paragraph()
    pb.add_run().add_break(WD_BREAK.PAGE)

    # Remove Appendix A entry from TOC only
    remove_paragraphs_with(doc, ["Приложение А. Техническое задание"])

    if sect_copy is not None:
        doc.element.body.append(sect_copy)

    replace_in_doc(doc)
    DOCS.mkdir(exist_ok=True)
    doc.save(str(OUT_FULL))
    print("Saved:", OUT_FULL)

    # Version without title page: remove the first block of title elements
    doc2 = Document(str(OUT_FULL))
    first_toc = next((i for i, p in enumerate(doc2.paragraphs) if p.text.strip() == "СОДЕРЖАНИЕ"), None)
    if first_toc is not None:
        for p in list(doc2.paragraphs[:first_toc]):
            p._element.getparent().remove(p._element)
    doc2.save(str(OUT_NOTITLE))
    print("Saved:", OUT_NOTITLE)


if __name__ == "__main__":
    main()
