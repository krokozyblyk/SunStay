from docx import Document
from pathlib import Path
import glob

p = Path([x for x in glob.glob(r"C:\pract\Kursovaya1,4kurs\docs\*SunStay.docx") if "~$" not in x][0])
d = Document(str(p))
words = ["Менеджер", "Хаускипинг", "Администратор", "Гость"]
for i, x in enumerate(d.paragraphs):
    if i <= 5700:
        continue
    t = x.text.strip()
    if any(w in t for w in words):
        print(i, "|", x.style.name, "|", repr(t[:65]))
