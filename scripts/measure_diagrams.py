from docx import Document
from docx.shared import Emu
from pathlib import Path
import glob

p = Path([x for x in glob.glob(r"C:\pract\Kursovaya1,4kurs\docs\*SunStay.docx") if "~$" not in x][0])
d = Document(str(p))
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# map inline shapes in document order to shapes list
shapes = list(d.inline_shapes)
si = 0
for i, para in enumerate(d.paragraphs):
    drawings = para._p.findall(".//" + W + "drawing")
    if not drawings:
        continue
    caption = ""
    for j in range(i + 1, min(i + 3, len(d.paragraphs))):
        t = d.paragraphs[j].text.strip()
        if t:
            caption = t
            break
    if si < len(shapes):
        s = shapes[si]
        si += 1
        w_cm = round(s.width / 360000, 2)
        h_cm = round(s.height / 360000, 2)
        ratio = round(s.width / s.height, 4) if s.height else 0
        if caption.startswith("Рисунок") or caption.startswith("Схема тестирования часть"):
            print(f"{caption[:60]:62s} {w_cm:>6} x {h_cm:<6} cm  ratio {ratio}")
