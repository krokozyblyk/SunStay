"""Rebuild the four separate appendix DOCX files from the enriched full PZ."""
from pathlib import Path
import glob

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PRILOZ = "".join(map(chr, [1055, 1088, 1080, 1083, 1086, 1078, 1077, 1085, 1080, 1077]))

OUTPUT = {
    PRILOZ + " Б": "Приложение_Б_Текст_программы.docx",
    PRILOZ + " В": "Приложение_В_Тестовые_испытания.docx",
    PRILOZ + " Г": "Приложение_Г_Руководство_пользователя.docx",
    PRILOZ + " Д": "Приложение_Д_Скрипт_базы_данных.docx",
}


def main():
    src = Path([x for x in glob.glob(str(DOCS / "*SunStay.docx")) if "~$" not in x][0])
    for key, name in OUTPUT.items():
        doc = Document(str(src))
        paras = list(doc.paragraphs)
        start_idx = None
        end_idx = len(paras)
        for i, p in enumerate(paras):
            t = p.text.strip()
            if p.alignment == 2 and t.startswith(PRILOZ + " "):
                if start_idx is None and t.startswith(key):
                    start_idx = i
                elif start_idx is not None:
                    end_idx = i
                    break
        if start_idx is None:
            print("SKIP", key)
            continue
        start_el = paras[start_idx]._p
        end_el = paras[end_idx]._p if end_idx < len(paras) else None

        body = doc.element.body
        children = list(body)
        i_start = children.index(start_el)
        i_end = children.index(end_el) if end_el is not None else len(children)
        for i, el in enumerate(children):
            if el.tag == qn("w:sectPr"):
                continue
            if i < i_start or i >= i_end:
                body.remove(el)

        out = DOCS / name
        doc.save(str(out))
        print("SAVED", name, out.stat().st_size)


if __name__ == "__main__":
    main()
