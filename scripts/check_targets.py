from docx import Document
from docx.oxml.ns import qn
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"
FIGURES = ["Схема архитектуры приложения", "Компоненты системы SunStay",
           "Схема потоков данных SunStay", "Логическая модель данных",
           "Функциональная схема системы", "Схема тестирования",
           "Процесс тестирования SunStay", "Схема процесса бронирования и заселения",
           "Диаграмма состояний номера", "Схема пользовательского интерфейса"]
SCHEMES = [f"Схема тестирования часть {n}" for n in range(1, 5)]

for name in ["Пояснительная_записка_SunStay.docx", "Приложение_В_Тестовые_испытания.docx"]:
    d = Document(str(DOCS / name))
    print("=" * 30, name)
    for topic in FIGURES + SCHEMES:
        hits = [i for i, p in enumerate(d.paragraphs) if topic in p.text]
        if not hits:
            print("  MISSING:", topic)
            continue
        i = hits[0]
        img = None
        for j in range(i - 1, max(-1, i - 5), -1):
            if d.paragraphs[j]._p.findall(".//" + qn("w:drawing")):
                img = j
                break
        print(f"  {i:5d} img={img}  {topic[:45]}")
