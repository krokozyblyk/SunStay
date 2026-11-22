"""Rebuild the no-title PZ from the current full PZ (keeps the user's own TOC)."""
from pathlib import Path
import glob
from docx import Document

DOCS = Path(__file__).resolve().parents[1] / "docs"
SODER = "".join(map(chr, [1057, 1086, 1076, 1077, 1088, 1078, 1072, 1085, 1080, 1077]))


def main():
    src = Path([x for x in glob.glob(str(DOCS / "*SunStay.docx")) if "~$" not in x][0])
    doc = Document(str(src))
    paras = list(doc.paragraphs)
    toc_idx = next((i for i, p in enumerate(paras)
                    if p.text.strip().lower() == SODER.lower()), None)
    if toc_idx is None:
        raise SystemExit("TOC heading not found")
    for p in paras[:toc_idx]:
        p._element.getparent().remove(p._element)
    out = DOCS / "Пояснительная_записка_без_титульника.docx"
    doc.save(str(out))
    print("SAVED", out.name, out.stat().st_size,
          "removed title paragraphs", toc_idx)


if __name__ == "__main__":
    main()
