from docx import Document
from pathlib import Path
import glob

p = Path([x for x in glob.glob(r"C:\pract\Kursovaya1,4kurs\docs\*SunStay.docx") if "~$" not in x][0])
d = Document(str(p))
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
print("inline_shapes", len(d.inline_shapes), "drawings", d.element.body.xml.count("<w:drawing"))
img_paras = [i for i, x in enumerate(d.paragraphs) if x._p.findall('.//' + W + "drawing")]
print("image paras", len(img_paras))
print(img_paras)
# captions around them
for i in img_paras:
    cap = d.paragraphs[i + 1].text.strip() if i + 1 < len(d.paragraphs) else ""
    print(i, "|", cap[:70])
