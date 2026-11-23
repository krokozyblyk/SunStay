from docx import Document
from pathlib import Path

D = Path(r"C:\pract\Kursovaya1,4kurs\docs")
B = Path(r"C:\Users\Redmibook\AppData\Local\Temp\opencode")
PAIRS = [
    ("Пояснительная_записка_SunStay.docx", "pre_diag_full.docx"),
    ("Пояснительная_записка_без_титульника.docx", "pre_diag_nt.docx"),
    ("Приложение_В_Тестовые_испытания.docx", "pre_diag_v.docx"),
]
for name, back in PAIRS:
    a = Document(str(D / name))
    b = Document(str(B / back))
    ta = [p.text for p in a.paragraphs]
    tb = [p.text for p in b.paragraphs]
    print(name, "text identical:", ta == tb, "| paras", len(ta), len(tb))
    if ta != tb:
        for i, (x, y) in enumerate(zip(ta, tb)):
            if x != y:
                print("  first diff", i, repr(x[:60]), "->", repr(y[:60]))
                break
