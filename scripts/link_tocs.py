"""Turn static TOC entries into clickable internal links. Title page untouched."""
from pathlib import Path
import re

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor

DOCS = Path(__file__).resolve().parents[1] / "docs"
FILES = ["Пояснительная_записка_SunStay.docx", "Пояснительная_записка_без_титульника.docx"]


def norm(s):
    return re.sub(r"[\s\u00a0]+", " ", s.strip()).lower()


def add_bookmark(para, name, idx):
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(idx))
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(idx))
    para._p.insert(0, start)
    para._p.append(end)


def link_entry(para, anchor):
    runs = list(para.runs)
    if not runs:
        return
    hl = OxmlElement("w:hyperlink")
    hl.set(qn("w:anchor"), anchor)
    for r in runs:
        r.font.color.rgb = RGBColor(0, 0, 0)
        r.font.underline = False
        hl.append(r._r)
    para._p.append(hl)


def process(name):
    doc = Document(str(DOCS / name))
    paras = list(doc.paragraphs)

    # headings and their bookmarks
    headings = []
    idx = 1000
    for p in paras:
        st = p.style.name
        if (st.endswith(("11", "21", "31")) or st.startswith("Heading")
                or p.text.strip().startswith("Приложение ")):
            t = p.text.strip()
            if t and len(t) < 120:
                bm = f"toc_bm_{idx}"
                add_bookmark(p, bm, idx)
                idx += 1
                headings.append((norm(t), bm))

    # TOC entries -> links
    linked = 0
    for p in doc.paragraphs:
        if not p.style.name.startswith(("toc", "Оглавление")):
            continue
        raw = p.text.replace("\u00a0", " ").strip()
        label = raw.split("\t")[0].strip()
        if not label:
            continue
        key = norm(label)
        bm = next((b for t, b in headings if t == key or t.startswith(key)), None)
        if bm:
            link_entry(p, bm)
            linked += 1

    doc.save(str(DOCS / name))
    print("LINKED", name, linked, "of", idx - 1000)


for f in FILES:
    process(f)
