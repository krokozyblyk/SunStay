from docx import Document
from pathlib import Path
import glob

p = Path([x for x in glob.glob(r"C:\pract\Kursovaya1,4kurs\docs\*SunStay.docx") if "~$" not in x][0])
d = Document(str(p))
markers = ["Схема тестирования", "ТРЕБОВАНИЯ К ТЕСТИРОВАНИЮ", "25 сценариев",
           "ЦЕЛЬ ИСПЫТАНИЙ", "Словарь данных базы данных", "Таблица 1. Модули",
           "Минимальные и рекомендованные", "2.2.5. Администратор базы данных"]
for i, x in enumerate(d.paragraphs):
    if i <= 5600:
        continue
    t = x.text.strip()
    if any(m in t for m in markers):
        print(i, "|", x.style.name, "|", t[:75])
