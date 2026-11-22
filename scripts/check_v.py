from docx import Document
from pathlib import Path
import glob

p = Path([x for x in glob.glob(r"C:\pract\Kursovaya1,4kurs\docs\*SunStay.docx") if "~$" not in x][0])
d = Document(str(p))
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
pre = "".join(map(chr, [1055, 1088, 1080, 1083, 1086, 1078, 1077, 1085, 1080, 1077]))

start = next(i for i, x in enumerate(d.paragraphs)
             if x.alignment == 2 and x.text.strip().startswith(pre + " В"))
end = next(i for i, x in enumerate(d.paragraphs)
           if i > start and x.alignment == 2 and x.text.strip().startswith(pre + " Г"))
print("V region", start, end)
for i in range(start, min(end, start + 140)):
    x = d.paragraphs[i]
    t = x.text.strip().replace("\t", "\\t")
    img = "IMG" if x._p.findall(".//" + W + "drawing") else ""
    if t or img:
        print(i, "|", x.style.name[:16], "|", img, "|", t[:85])
