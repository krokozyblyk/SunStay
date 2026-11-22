from docx import Document
from pathlib import Path

BASE = Path(r"C:\Users\Redmibook\Desktop\Zadanie_tz\09.02.07 П-3-23 Злобин Д.В. КП РПМ\Документация")
f = next(BASE.glob("Приложение В*.docx"))
d = Document(str(f))
print("TABLES", len(d.tables))
for ti, t in enumerate(d.tables):
    print("=" * 70)
    print("TABLE", ti, "rows", len(t.rows), "cols", len(t.columns))
    hdr = [c.text.strip().replace("\n", " ") for c in t.rows[0].cells]
    print("HEADER:", hdr)
    for r in t.rows[1:4]:
        print("  ", [c.text.strip().replace("\n", " ")[:38] for c in r.cells])
    if len(t.rows) > 5:
        print("   ...")
        for r in t.rows[-2:]:
            print("  ", [c.text.strip().replace("\n", " ")[:38] for c in r.cells])
