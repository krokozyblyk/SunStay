from docx import Document
from pathlib import Path
import glob

DOCS = Path(__file__).resolve().parents[1] / "docs"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SODER = "".join(map(chr, [1057, 1086, 1076, 1077, 1088, 1078, 1072, 1085, 1080, 1077]))
BACKUP = Path(r"C:\Users\Redmibook\AppData\Local\Temp\opencode\backup_full_before_enrich.docx")

files = [DOCS / "Пояснительная_записка_SunStay.docx",
         DOCS / "Пояснительная_записка_без_титульника.docx"]
files += sorted(DOCS.glob("Приложение_*.docx"))

for f in files:
    d = Document(str(f))
    toc = [p for p in d.paragraphs if p.style.name.startswith(SODER)]
    unlinked = sum(1 for p in toc if not p._p.findall(W + "hyperlink"))
    shading = d.element.body.xml.count("<w:shd")
    print(f.name)
    print("  paras", len(d.paragraphs), "tables", len(d.tables),
          "imgs", len(d.inline_shapes), "shading", shading)
    print("  TOC", len(toc), "unlinked", unlinked)

full = Document(str(files[0]))
old = Document(str(BACKUP))
t1 = [(p.text, p.style.name, str(p.alignment)) for p in old.paragraphs[:26]]
t2 = [(p.text, p.style.name, str(p.alignment)) for p in full.paragraphs[:26]]
print("TITLE PAGE UNCHANGED:", t1 == t2)
