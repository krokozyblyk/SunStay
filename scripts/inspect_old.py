from docx import Document
from pathlib import Path
import glob

BASE = Path(r"C:\Users\Redmibook\Desktop\Zadanie_tz\09.02.07 П-3-23 Злобин Д.В. КП РПМ\Документация")

def find(prefix):
    for f in BASE.glob("*.docx"):
        if f.name.startswith(prefix) and "Пояснительная" not in f.name:
            return f
    return None

for key in ["Приложение Б", "Приложение В", "Приложение Г", "Приложение Д"]:
    f = find(key)
    if not f:
        print("NOT FOUND", key)
        continue
    d = Document(str(f))
    print("=" * 70)
    print(key, "paras", len(d.paragraphs), "tables", len(d.tables), "imgs", len(d.inline_shapes))
    print("-" * 70)
    for i, p in enumerate(d.paragraphs[:55]):
        t = p.text.strip().replace("\t", "\\t")
        if t:
            print(i, "|", p.style.name, "|", t[:70])
