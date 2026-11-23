"""Replace only the diagram images inside the finished DOCX files.

Captions, numbering, title page, TOC, text and tables stay untouched.
"""
from pathlib import Path
import glob

from docx import Document
from docx.shared import Emu
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DIAG = DOCS / "diagrams"
WP_EXTENT = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent"

# topic substring -> new image
FIGURES = [
    ("Схема архитектуры приложения", "architecture.png"),
    ("Компоненты системы SunStay", "components.png"),
    ("Схема потоков данных SunStay", "dataflow.png"),
    ("Логическая модель данных", "erd.png"),
    ("Функциональная схема системы", "functional.png"),
    ("Схема тестирования", "testpyramid.png"),
    ("Процесс тестирования SunStay", "testing-flow.png"),
    ("Схема процесса бронирования и заселения", "booking-flow.png"),
    ("Диаграмма состояний номера", "room-states.png"),
    ("Схема пользовательского интерфейса", "uimap.png"),
]
SCHEMES = [(f"Схема тестирования часть {n}", f"testing-scheme-{n}.png") for n in range(1, 5)]

FILES = [
    DOCS / "Пояснительная_записка_SunStay.docx",
    DOCS / "Пояснительная_записка_без_титульника.docx",
    DOCS / "Приложение_В_Тестовые_испытания.docx",
]


def replace_near(doc, caption_fragment, image_path, scheme=False):
    paras = doc.paragraphs
    cap_i = None
    for i, p in enumerate(paras):
        t = p.text.strip()
        if scheme:
            if t.startswith("Схема тестирования часть") and caption_fragment in t:
                cap_i = i
                break
        else:
            if t.startswith("Рисунок") and caption_fragment in t:
                cap_i = i
                break
    if cap_i is None:
        return False
    # find the nearest preceding paragraph that contains a drawing
    img_p = None
    for j in range(cap_i - 1, max(-1, cap_i - 5), -1):
        if paras[j]._p.findall(".//" + qn("w:drawing")):
            img_p = paras[j]
            break
    if img_p is None:
        return False
    ext = img_p._p.find(".//" + WP_EXTENT)
    cx = int(ext.get("cx")) if ext is not None else 0
    # remove old runs/hyperlinks, keep paragraph properties and bookmarks
    for child in list(img_p._p):
        if child.tag in (qn("w:r"), qn("w:hyperlink")):
            img_p._p.remove(child)
    run = img_p.add_run()
    if cx:
        run.add_picture(str(image_path), width=Emu(cx))
    else:
        run.add_picture(str(image_path))
    return True


def process(path):
    doc = Document(str(path))
    done = 0
    for topic, fname in FIGURES:
        target = DIAG / fname
        if target.exists() and replace_near(doc, topic, target):
            done += 1
    for topic, fname in SCHEMES:
        target = DIAG / fname
        if target.exists() and replace_near(doc, topic, target, scheme=True):
            done += 1
    doc.save(str(path))
    print("UPDATED", path.name, "images:", done)


def main():
    for f in FILES:
        if f.exists():
            process(f)


if __name__ == "__main__":
    main()
