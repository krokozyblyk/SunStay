from docx import Document
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"
for f in sorted(DOCS.glob("Приложение_*.docx")):
    d = Document(str(f))
    print("=" * 55)
    print(f.name, "paras", len(d.paragraphs), "tables", len(d.tables), "imgs", len(d.inline_shapes))
    for i, p in enumerate(d.paragraphs[:16]):
        t = p.text.strip()
        if t:
            print(" ", i, "|", p.style.name, "|", t[:70])
