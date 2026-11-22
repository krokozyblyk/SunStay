from docx import Document
from pathlib import Path
import glob

DOCS = Path(__file__).resolve().parents[1] / "docs"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SODER = "".join(map(chr, [1057, 1086, 1076, 1077, 1088, 1078, 1072, 1085, 1080, 1077]))
PRILOZ = "".join(map(chr, [1055, 1088, 1080, 1083, 1086, 1078, 1077, 1085, 1080, 1077]))
BACKUP = Path(r"C:\Users\Redmibook\AppData\Local\Temp\opencode\backup_full_before_enrich.docx")


def title_paras(doc):
    out = []
    for p in doc.paragraphs[:26]:
        out.append((p.text, p.style.name, str(p.alignment)))
    return out


def check(path):
    doc = Document(str(path))
    print("=" * 60)
    print(path.name)
    print("paras", len(doc.paragraphs), "tables", len(doc.tables), "imgs", len(doc.inline_shapes))
    xml = doc.element.body.xml
    print("shading", xml.count("<w:shd"), "hyperlinks", xml.count("<w:hyperlink"))
    # title comparison
    if "SunStay.docx" in path.name and "без" not in path.name:
        old = Document(str(BACKUP))
        a, b = title_paras(old), title_paras(doc)
        print("TITLE IDENTICAL:", a == b)
        if a != b:
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    print("  diff at", i, x, "->", y)
    # appendix TOC link status
    paras = doc.paragraphs
    toc = [(i, p) for i, p in enumerate(paras)
           if p.style.name.startswith(SODER + " приложения")]
    plain = [(i, p.text[:45]) for i, p in toc if not p._p.findall(W + "hyperlink")]
    print("appendix TOC entries", len(toc), "not linked", len(plain))
    for i, t in plain[:10]:
        print("   PLAIN", i, repr(t))
    # markers
    txt = "\n".join(p.text for p in paras)
    for marker in ["Схема тестирования часть 1", "Схема тестирования часть 4",
                   "25 сценариев", "Словарь данных базы данных",
                   "Минимальные и рекомендованные требования", "2.2.5. Администратор базы данных"]:
        print("  ", marker[:35], "->", marker in txt)


for name in ["Пояснительная_записка_SunStay.docx", "Пояснительная_записка_без_титульника.docx"]:
    check(DOCS / name)
