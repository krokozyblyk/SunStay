"""Point main-TOC appendix entries at the actual appendix title pages."""
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

DOCS = Path(__file__).resolve().parents[1] / "docs"
FILES = ["Пояснительная_записка_SunStay.docx", "Пояснительная_записка_без_титульника.docx"]
PREFIX = "Приложение"
APP_WORD = "".join(map(chr, [1055, 1088, 1080, 1083, 1086, 1078, 1077, 1085, 1080, 1077]))


def add_bookmark(para, name, idx):
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(idx))
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(idx))
    para._p.insert(0, start)
    para._p.append(end)


def process(name):
    doc = Document(str(DOCS / name))
    paras = list(doc.paragraphs)

    # find real appendix title paragraphs (start with "Приложение", right aligned)
    targets = {}
    idx = 3000
    for p in paras:
        t = p.text.strip()
        if t.startswith(PREFIX) and len(t) < 120 and p.alignment == 2:
            bm = f"appendix_{idx}"
            add_bookmark(p, bm, idx)
            idx += 1
            targets[t.split("\t")[0].strip().lower()] = bm

    # main TOC entries that start with "Приложение" -> set their hyperlink anchor
    fixed = 0
    for p in doc.paragraphs:
        t = p.text.replace("\u00a0", " ").strip()
        if not t.lower().startswith(PREFIX.lower()):
            continue
        label = t.split("\t")[0].strip().lower()
        bm = targets.get(label)
        if not bm:
            # try "starts with" match
            bm = next((v for k, v in targets.items() if k.startswith(label[:20])), None)
        if not bm:
            continue
        for hl in p._p.findall(qn("w:hyperlink")):
            hl.set(qn("w:anchor"), bm)
            fixed += 1
        # if there is no hyperlink yet, wrap the runs
        if not p._p.findall(qn("w:hyperlink")) and p.runs:
            hl = OxmlElement("w:hyperlink")
            hl.set(qn("w:anchor"), bm)
            for r in list(p.runs):
                hl.append(r._r)
            p._p.append(hl)
            fixed += 1

    # remove TOC line for Appendix A (no such document)
    for para in list(doc.paragraphs):
        if para.text.replace(chr(0xa0), ' ').strip().startswith(PREFIX + ' ' + chr(1040)) and chr(1058)+chr(1077)+chr(1093)+chr(1085)+chr(1080)+chr(1095)+chr(1077)+chr(1089)+chr(1082)+chr(1086)+chr(1077) in para.text:
            para._element.getparent().remove(para._element)

    doc.save(str(DOCS / name))
    print("LINKS FIXED", name, fixed, "targets", list(targets.values()))


for f in FILES:
    process(f)
