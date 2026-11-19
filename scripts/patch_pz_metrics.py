from pathlib import Path

from docx import Document

PATH = Path(r"C:\pract\Kursovaya1,4kurs\docs\Пояснительная_записка_SunStay.docx")

REPLACEMENTS = {
    "p95 менее 100 мс": "p95 не более 150 мс",
    "395,26": "264,40",
    "43,43": "67,11",
    "70,99": "111,29",
    "387,90": "284,07",
    "24,60": "34,02",
    "38,09": "66,49",
    "p95 70,99 и 38,09 мс": "p95 111,29 и 66,49 мс",
}


def replace_paragraph(paragraph) -> None:
    text = paragraph.text
    if not any(old in text for old in REPLACEMENTS):
        return
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    for run in list(paragraph.runs):
        run._element.getparent().remove(run._element)
    paragraph.add_run(text)


def main() -> None:
    doc = Document(str(PATH))
    for paragraph in doc.paragraphs:
        replace_paragraph(paragraph)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    replace_paragraph(paragraph)
    doc.save(str(PATH))
    print("PZ metrics patched")


if __name__ == "__main__":
    main()
