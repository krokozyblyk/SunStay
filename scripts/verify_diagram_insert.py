from pathlib import Path
import hashlib
from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DIAG = DOCS / "diagrams"
BACK = Path(r"C:\Users\Redmibook\AppData\Local\Temp\opencode")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

TARGETS = [
    ("Рисунок", "Схема архитектуры приложения", "architecture.png"),
    ("Рисунок", "Компоненты системы SunStay", "components.png"),
    ("Рисунок", "Схема потоков данных SunStay", "dataflow.png"),
    ("Рисунок", "Логическая модель данных", "erd.png"),
    ("Рисунок", "Функциональная схема системы", "functional.png"),
    ("Рисунок", "Схема тестирования", "testpyramid.png"),
    ("Рисунок", "Процесс тестирования SunStay", "testing-flow.png"),
    ("Рисунок", "Схема процесса бронирования и заселения", "booking-flow.png"),
    ("Рисунок", "Диаграмма состояний номера", "room-states.png"),
    ("Рисунок", "Схема пользовательского интерфейса", "uimap.png"),
] + [("Схема", f"Схема тестирования часть {n}", f"testing-scheme-{n}.png") for n in range(1, 5)]


def find_caption(doc, prefix, frag):
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if prefix == "Рисунок":
            if t.startswith("Рисунок") and frag in t:
                return i
        else:
            if t.startswith("Схема тестирования часть") and frag in t:
                return i
    return None


def image_hash(doc, cap_i):
    for j in range(cap_i - 1, max(-1, cap_i - 5), -1):
        blips = doc.paragraphs[j]._p.findall(".//" + A + "blip")
        if blips:
            rid = blips[0].get(R + "embed")
            part = doc.part.related_parts[rid]
            return hashlib.md5(part.blob).hexdigest()
    return None


for name, back in [("Пояснительная_записка_SunStay.docx", "pre_diag_full.docx"),
                   ("Пояснительная_записка_без_титульника.docx", "pre_diag_nt.docx"),
                   ("Приложение_В_Тестовые_испытания.docx", "pre_diag_v.docx")]:
    doc = Document(str(DOCS / name))
    old = Document(str(BACK / back))
    print("=" * 45, name)
    print("paras", len(doc.paragraphs), "tables", len(doc.tables),
          "imgs", len(doc.inline_shapes),
          "| before:", len(old.paragraphs), len(old.tables), len(old.inline_shapes))
    ok = 0
    for prefix, frag, fname in TARGETS:
        cap = find_caption(doc, prefix, frag)
        if cap is None:
            continue
        got = image_hash(doc, cap)
        want = hashlib.md5((DIAG / fname).read_bytes()).hexdigest()
        status = "OK" if got == want else "DIFF"
        if got == want:
            ok += 1
        print(f"  {status:4s} {frag[:48]}")
    print("matched", ok)
    # TOC links unchanged?
    print("TOC links now", doc.element.body.xml.count("<w:hyperlink"),
          "before", old.element.body.xml.count("<w:hyperlink"))
