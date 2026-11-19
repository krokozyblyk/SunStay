from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path(r"C:\Users\Redmibook\Downloads\Титульный лист КП МДК 11.01 ТРЗБД 2023.docx")
OUTPUT = ROOT / "docs" / "Пояснительная_записка_SunStay.docx"
SHOTS = ROOT / "docs" / "screenshots"
DIAGRAMS = ROOT / "docs" / "diagrams"

FIG_COUNTER = 0


def set_run_font(run, size=14, bold=None, italic=None, color=None):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def setup_styles(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(14)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    normal.paragraph_format.first_line_indent = Cm(1.25)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.space_after = Pt(0)

    for name, size in (("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 14)):
        try:
            style = doc.styles[name]
        except KeyError:
            style = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.first_line_indent = Cm(0)
        style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.keep_with_next = True
        level = {"Heading 1": 0, "Heading 2": 1, "Heading 3": 2}[name]
        p_pr = style._element.get_or_add_pPr()
        outline = p_pr.find(qn("w:outlineLvl"))
        if outline is None:
            outline = OxmlElement("w:outlineLvl")
            p_pr.append(outline)
        outline.set(qn("w:val"), str(level))

    doc.styles["Heading 1"].paragraph_format.space_before = Pt(12)
    doc.styles["Heading 1"].paragraph_format.page_break_before = True
    doc.styles["Heading 2"].paragraph_format.space_before = Pt(10)
    doc.styles["Heading 3"].paragraph_format.space_before = Pt(8)

    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(3)
        section.right_margin = Cm(1.5)


def add_page_numbers(doc: Document) -> None:
    for section in doc.sections:
        footer = section.footer
        paragraph = footer.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        set_run_font(run, 12)
        fld_begin = OxmlElement("w:fldChar")
        fld_begin.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = "PAGE"
        fld_end = OxmlElement("w:fldChar")
        fld_end.set(qn("w:fldCharType"), "end")
        run._r.append(fld_begin)
        run._r.append(instr)
        run._r.append(fld_end)


def add_toc(doc: Document) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "Обновите поле (F9), чтобы построить содержание."
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(text)
    run._r.append(fld_end)


def h1(doc: Document, text: str) -> None:
    paragraph = doc.add_heading(text, level=1)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.first_line_indent = Cm(0)


def h2(doc: Document, text: str) -> None:
    paragraph = doc.add_heading(text, level=2)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.first_line_indent = Cm(0)


def h3(doc: Document, text: str) -> None:
    paragraph = doc.add_heading(text, level=3)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.first_line_indent = Cm(0)


def p(doc: Document, text: str) -> None:
    paragraph = doc.add_paragraph()
    run = paragraph.add_run(text)
    set_run_font(run, 14)


def bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(1.25)
        paragraph.paragraph_format.first_line_indent = Cm(-0.5)
        paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = paragraph.add_run(f"• {item}")
        set_run_font(run, 14)


def numbered(doc: Document, items: list[str]) -> None:
    for index, item in enumerate(items, 1):
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(1.25)
        paragraph.paragraph_format.first_line_indent = Cm(-0.5)
        paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = paragraph.add_run(f"{index}. {item}")
        set_run_font(run, 14)


def shade(cell, color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tr_pr.append(tbl_header)


def table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float] | None = None) -> None:
    table_obj = doc.add_table(rows=1, cols=len(headers))
    table_obj.style = "Table Grid"
    table_obj.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_cells = table_obj.rows[0].cells
    for index, header in enumerate(headers):
        cell = header_cells[index]
        cell.text = ""
        run = cell.paragraphs[0].add_run(header)
        set_run_font(run, 12, bold=True)
        cell.paragraphs[0].paragraph_format.first_line_indent = Cm(0)
        cell.paragraphs[0].paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        shade(cell, "F3EEE6")
    repeat_header(table_obj.rows[0])
    for row_data in rows:
        cells = table_obj.add_row().cells
        for index, value in enumerate(row_data):
            cell = cells[index]
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(value))
            set_run_font(run, 12)
            cell.paragraphs[0].paragraph_format.first_line_indent = Cm(0)
            cell.paragraphs[0].paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
    if widths:
        for row in table_obj.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Cm(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def figure(doc: Document, path: Path, caption: str, width_cm: float = 13.5) -> None:
    global FIG_COUNTER
    FIG_COUNTER += 1
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.keep_together = True
    run = paragraph.add_run()
    run.add_picture(str(path), width=Cm(width_cm))
    caption_paragraph = doc.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_paragraph.paragraph_format.first_line_indent = Cm(0)
    caption_paragraph.paragraph_format.space_after = Pt(8)
    caption_paragraph.paragraph_format.keep_together = True
    caption_run = caption_paragraph.add_run(f"Рисунок {FIG_COUNTER} – {caption}")
    set_run_font(caption_run, 12)


def replace_paragraph_text(paragraph, new_text: str) -> None:
    for run in list(paragraph.runs):
        run._element.getparent().remove(run._element)
    run = paragraph.add_run(new_text)
    set_run_font(run, 14, color="000000")


def prepare_title_page(doc: Document) -> None:
    for paragraph in doc.paragraphs:
        if "Тема:" in paragraph.text:
            replace_paragraph_text(
                paragraph,
                "Тема: «Разработка программного комплекса для автоматизации деятельности гостиницы «SunStay»»",
            )
        for run in paragraph.runs:
            run.text = run.text.replace("2023", "2026")
            run.text = run.text.replace("Листов: 0", "Листов: 43")

    for table_obj in doc.tables:
        table_obj.autofit = False
        try:
            table_obj.columns[0].width = Cm(2.0)
            table_obj.columns[1].width = Cm(13.5)
        except Exception:
            pass
        for row in table_obj.rows:
            tr_pr = row._tr.get_or_add_trPr()
            if tr_pr.find(qn("w:cantSplit")) is None:
                tr_pr.append(OxmlElement("w:cantSplit"))
            for cell in row.cells:
                for paragraph in list(cell.paragraphs):
                    if "Г.Ю. Волкова" in paragraph.text:
                        replace_paragraph_text(paragraph, "__________ / Л.А. Соколова")
                    elif "И.И. Иванов" in paragraph.text or "И.И" in paragraph.text:
                        replace_paragraph_text(paragraph, "студент гр. П-3-23 __________ / Д.В. Злобин")
                    elif "2023" in paragraph.text:
                        replace_paragraph_text(paragraph, "«____» ____________ 2026 г.")
                    elif not paragraph.text.strip() and len(cell.paragraphs) > 5:
                        paragraph._element.getparent().remove(paragraph._element)

    paragraphs = list(doc.paragraphs)
    first_content = next((i for i, item in enumerate(paragraphs) if "Курсовой проект" in item.text), None)
    if first_content is not None:
        for item in paragraphs[:first_content]:
            if not item.text.strip():
                item._element.getparent().remove(item._element)

    paragraphs = list(doc.paragraphs)
    try:
        start = next(i for i, item in enumerate(paragraphs) if item.text.strip().startswith("Листов:"))
        end = next(i for i, item in enumerate(paragraphs) if item.text.strip() == "2026" and i > start)
        for item in paragraphs[start + 1:end]:
            if not item.text.strip():
                item._element.getparent().remove(item._element)
    except StopIteration:
        pass




def build() -> None:
    doc = Document(str(TEMPLATE))
    setup_styles(doc)
    prepare_title_page(doc)
    add_page_numbers(doc)
    doc.add_page_break()

    toc_title = doc.add_paragraph()
    toc_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    toc_title.paragraph_format.first_line_indent = Cm(0)
    toc_run = toc_title.add_run("СОДЕРЖАНИЕ")
    set_run_font(toc_run, 16, bold=True)
    add_toc(doc)

    # ------------------------------------------------------------------ ВВЕДЕНИЕ
    h1(doc, "ВВЕДЕНИЕ")
    p(doc, "Современный гостиничный бизнес работает в условиях высокой конкуренции, сезонных колебаний спроса и постоянного роста требований к качеству сервиса. Небольшой отель вынужден одновременно управлять номерным фондом, тарифами, бронированиями, заездами и выездами гостей, дополнительными услугами, платежами, уборкой номеров и отчётностью. Если эти процессы ведутся в разрозненных таблицах, мессенджерах и бумажных журналах, возрастает риск двойных бронирований, потери платежей, ошибок в счетах и задержек при заселении.")
    p(doc, "Актуальность работы обусловлена необходимостью перевести перечисленные процессы в единую информационную систему, которая обеспечивает централизованное хранение данных, серверную проверку бизнес-правил, разграничение прав доступа, прозрачный аудит действий и автоматическое формирование отчётности. Для гостиницы «SunStay» такая система позволяет сократить время обслуживания гостя, исключить пересечение броней одного номера и повысить управляемость загрузкой.")
    p(doc, "Объектом исследования является деятельность бутик-отеля «SunStay»: номерной фонд, бронирования, проживание, хаускипинг, дополнительные услуги и расчёты с гостями. Предметом исследования являются методы и средства проектирования и реализации клиент-серверной информационной системы на базе реляционной СУБД.")
    p(doc, "Цель курсового проекта — разработать защищённую клиент-серверную информационную систему гостиницы «SunStay», обеспечивающую автоматизацию бронирования, заселения, выселения, биллинга, хаускипинга, отчётности и администрирования.")
    p(doc, "Для достижения цели поставлены следующие задачи:")
    numbered(doc, [
        "проанализировать предметную область, роли пользователей и бизнес-процессы гостиницы;",
        "спроектировать реляционную базу данных, нормализованную до третьей нормальной формы, и построить ER-диаграмму;",
        "реализовать серверную логику: ограничения целостности, представления, функции, хранимые процедуры и триггеры;",
        "обеспечить безопасность: RBAC на пять ролей, хэширование паролей, JWT-сессии, аудит и резервное копирование;",
        "разработать REST API и клиентское веб-приложение с поддержкой двух тем и языков RU/EN;",
        "реализовать подсистему статистики и отчётности с визуализациями и экспортом;",
        "провести функциональное, интеграционное, нагрузочное и security-тестирование;",
        "подготовить пояснительную записку и эксплуатационную документацию.",
    ])
    p(doc, "Пояснительная записка состоит из введения, трёх разделов, заключения, списка использованных источников и приложений. В общей части описаны предметная область, требования и средства разработки. В специальной части приведены проектирование базы данных, архитектура, серверная логика, механизмы защиты, API, интерфейс и отчётность. В технологической части описаны стек, отладка, защитное программирование и DevOps-схема. Приложения содержат ссылки на тексты программы, тестовые материалы и руководство пользователя.")

    # ------------------------------------------------------------------ 1 ОБЩАЯ ЧАСТЬ
    h1(doc, "1 ОБЩАЯ ЧАСТЬ")
    h2(doc, "1.1 Постановка задачи")
    p(doc, "Гостиница «SunStay» — бутик-отель на 48 номеров, расположенный в Санкт-Петербурге. В отеле работают пять категорий пользователей: гость, менеджер службы приёма, сотрудник хаускипинга, управляющий отелем и администратор базы данных. Гость взаимодействует с отелем через публичный сайт, остальные роли — через закрытую часть системы.")
    p(doc, "До внедрения системы учёт велся в Excel, телефонных звонках и мессенджерах. Это приводило к следующим проблемам: пересечение броней одного номера, несвоевременное обновление статусов уборки, расхождения между начислениями и платежами, отсутствие единого журнала действий сотрудников и ручная подготовка отчётов. Требуется единая информационная система, работающая как веб-приложение и использующая PostgreSQL в качестве центрального хранилища данных.")
    p(doc, "Система должна обеспечивать: поиск доступности номеров, оформление и оплату брони, подтверждение и отмену броней, заселение и выселение, открытие и закрытие folio, приём платежей и возвратов, заказ дополнительных услуг, управление заданиями хаускипинга и техобслуживания, учёт расходных материалов, ночной аудит, отчётность, администрирование пользователей и резервное копирование.")
    p(doc, "Ключевые бизнес-правила: запрет пересечения активных броней одного физического номера; заселение только по подтверждённой брони; начисление проживания только для заселённой брони; невозможность списания расходных материалов больше остатка; запрет изменения закрытого бизнес-дня без специальных прав; все значимые изменения фиксируются в журнале аудита.")

    h2(doc, "1.2 Предметная область и бизнес-процессы")
    p(doc, "Основные процессы гостиницы образуют замкнутый цикл: поиск и бронирование → подтверждение → заезд → проживание и услуги → выезд и закрытие счёта → уборка и подготовка номера к следующей продаже. Параллельно выполняются ночной аудит, техническое обслуживание, управление тарифами, отчётность и администрирование.")
    table(doc, ["Процесс", "Участники", "Результат"], [
        ["Поиск и бронирование", "Гость, менеджер", "Бронь со статусом NEW или CONFIRMED, закреплённый номер и тариф"],
        ["Заселение", "Менеджер", "Запись check-in, открытый folio, статус номера «Заселён»"],
        ["Проживание и услуги", "Гость, менеджер", "Заказы услуг, начисления в folio, платежи"],
        ["Ночной аудит", "Менеджер", "Начисление проживания, обработка no-show, закрытие бизнес-дня"],
        ["Выселение", "Менеджер", "Закрытый folio, финальный платёж, статус номера «Грязный», задание хаускипингу"],
        ["Хаускипинг", "Сотрудник хаускипинга", "Выполненное задание, статус «Готов», списание расходников"],
        ["Техобслуживание", "Хаускипинг, менеджер", "Заявка на ремонт и её статус"],
        ["Отчётность", "Менеджер, управляющий, администратор БД", "Дашборды и отчёты по загрузке, ADR, RevPAR, отменам"],
    ], widths=[4.2, 4.2, 7.1])
    p(doc, "Процесс бронирования должен быть атомарным: проверка доступности и создание брони выполняются в одной транзакции. Для защиты от гонки при параллельных запросах используется exclusion-ограничение PostgreSQL на пересечение диапазонов дат для активных статусов брони. Это гарантирует, что даже при одновременных запросах двух менеджеров один и тот же номер не будет продан дважды.")

    h2(doc, "1.3 Входные и выходные данные")
    p(doc, "Входные данные системы можно разделить на справочные, операционные и служебные. Справочные данные меняются редко, операционные — в ходе ежедневной работы, служебные — при администрировании.")
    table(doc, ["Группа", "Данные"], [
        ["Справочники", "Типы номеров, номера, удобства, статусы номеров, причины блокировки, тарифные планы, услуги, единицы измерения, промокоды, причины отмены"],
        ["Гости", "ФИО, документ, телефон, email, согласие на обработку ПДн, привязка к учётной записи"],
        ["Бронирования", "Гость, номер, тариф, даты заезда/выезда, статус, источник, количество взрослых и детей, промокод"],
        ["Проживание", "Факт заселения, документ, депозит, факт выселения, дополнительные гости"],
        ["Биллинг", "Folio, строки начислений, платежи, возвраты, способы оплаты"],
        ["Хаускипинг", "Задания на уборку, исполнитель, приоритет, статус, расходные материалы и их остатки"],
        ["Техобслуживание", "Номер, описание неисправности, приоритет, исполнитель, статус"],
        ["Администрирование", "Пользователи, роли, права, настройки, сессии, журнал аудита, резервные копии"],
    ], widths=[4.0, 11.5])
    p(doc, "Выходными данными являются результаты поиска доступности, подтверждение брони, карточка брони, folio с балансом, PDF-счёт, задания хаускипинга, уведомления об ошибках, дашборды и отчёты. Отчёты экспортируются в CSV и PNG; счета — в PDF. Для администратора доступны журнал аудита и сведения о состоянии базы данных.")
    table(doc, ["Выходные данные", "Форма представления"], [
        ["Результаты поиска номеров", "JSON API и карточки на сайте"],
        ["Подтверждение брони", "Экран подтверждения и запись в БД"],
        ["Folio и баланс", "Экран, JSON API, PDF-счёт"],
        ["Отчёты по загрузке, ADR/RevPAR, отменам", "Графики, таблицы, CSV, PNG"],
        ["Статусы номеров и задания хаускипинга", "Канбан-доска и API"],
        ["Журнал аудита", "Таблица с фильтрами и CSV-экспорт"],
        ["Резервные копии", "Файлы .dump и список в админ-панели"],
    ], widths=[7.5, 8.0])

    h2(doc, "1.4 Роли пользователей и сценарии")
    p(doc, "В системе реализована ролевая модель на пять ролей. Права хранятся в таблицах permissions и role_permissions и проверяются на сервере при каждом запросе. Клиентское скрытие кнопок не является механизмом защиты.")
    table(doc, ["Роль", "Основные возможности"], [
        ["Гость", "Поиск доступности, бронирование и оплата, свои брони, счета, заказ услуг, отмена брони, настройки профиля"],
        ["Менеджер", "Все брони, подтверждение и отмена, заселение и выселение, folio, платежи и возвраты, шахматка, хаускипинг, ночной аудит, отчёты"],
        ["Хаускипинг", "Задания на уборку, статусы номеров, заявки на ремонт, расходные материалы"],
        ["Управляющий отелем", "Все операционные функции менеджера, тарифы, услуги, промокоды, сотрудники, отчёты, аудит в режиме чтения"],
        ["Администратор БД", "Пользователи и роли, справочники, аудит, резервное копирование, мониторинг, настройки системы"],
    ], widths=[4.0, 11.5])
    p(doc, "Типовые сценарии:")
    bullets(doc, [
        "Гость выбирает даты, тип номера и оформляет бронь с онлайн-оплатой; система проверяет доступность и создаёт подтверждённую бронь.",
        "Менеджер заселяет гостя по подтверждённой брони, проверяет документ, принимает депозит и открывает folio.",
        "Гость заказывает завтрак через личный кабинет; услуга и строка начисления создаются одной транзакцией.",
        "Менеджер запускает ночной аудит; система начисляет проживание, обрабатывает no-show и закрывает бизнес-день.",
        "Менеджер выселяет гостя, принимает финальный платёж, закрывает folio и создаёт задание на уборку.",
        "Хаускипинг завершает задание, списывает расходники и переводит номер в статус «Готов».",
        "Администратор БД создаёт резервную копию и восстанавливает базу на тестовом стенде.",
    ])

    h2(doc, "1.5 Средства разработки")
    p(doc, "При выборе средств разработки учитывались требования к надёжности, безопасности, поддержке транзакций и возможности развернуть систему в контейнерах. Выбранный стек представлен в таблице.")
    table(doc, ["№", "Тип средства", "Название", "Назначение"], [
        ["1", "Операционная система", "Windows 11", "Разработка и локальный запуск"],
        ["2", "СУБД", "PostgreSQL 16", "Хранение данных, транзакции, процедуры, триггеры"],
        ["3", "Язык серверной части", "Python 3.13", "Реализация FastAPI-сервисов"],
        ["4", "Серверный фреймворк", "FastAPI", "REST API, OpenAPI, зависимости, валидация"],
        ["5", "Драйвер БД", "psycopg 3", "Подключение к PostgreSQL, пул соединений"],
        ["6", "Аутентификация", "JWT, bcrypt", "Access/refresh-сессии, хэширование паролей"],
        ["7", "Клиентская часть", "React 18 + TypeScript", "SPA для гостя и сотрудников"],
        ["8", "Сборка", "Vite 6", "Сборка и dev-сервер"],
        ["9", "Стили", "Tailwind CSS", "Дизайн-токены, адаптивная вёрстка"],
        ["10", "Графики", "Recharts", "Визуализация отчётов"],
        ["11", "Контейнеризация", "Docker Compose", "PostgreSQL, API, analytics, web, Adminer"],
        ["12", "Веб-сервер", "Nginx", "Раздача статики и reverse proxy"],
        ["13", "Контроль версий", "Git", "История изменений"],
        ["14", "Документирование", "Office CLI, python-docx", "Сборка пояснительной записки"],
    ], widths=[1.2, 4.0, 4.0, 6.3])
    p(doc, "Разработка велась на ноутбуке Redmi Book 16 2024 (Intel Core i5, 16 ГБ ОЗУ, SSD 512 ГБ, Windows 11). Для проверки использовались браузер Microsoft Edge, терминал PowerShell, Docker Desktop и psql внутри контейнера.")

    # ------------------------------------------------------------------ 2 СПЕЦИАЛЬНАЯ ЧАСТЬ
    h1(doc, "2 СПЕЦИАЛЬНАЯ ЧАСТЬ")
    h2(doc, "2.1 Внешняя спецификация")
    h3(doc, "2.1.1 Описание задачи")
    p(doc, "Разрабатываемая система представляет собой веб-приложение, состоящее из публичной части для гостей и закрытой части для сотрудников. Публичная часть позволяет просматривать номерной фонд, искать доступность, оформлять бронь и оплачивать проживание. Закрытая часть реализует рабочие места менеджера, хаускипинга, управляющего отелем и администратора БД.")
    p(doc, "С точки зрения архитектуры система является клиент-серверной. Клиент — React SPA, сервер — два FastAPI-сервиса: core API для бизнес-операций и analytics API для отчётов. Оба сервиса работают с одной базой PostgreSQL, но используют разные роли СУБД: приложение и аналитика. Это снижает риск случайного изменения данных аналитическим сервисом.")
    h3(doc, "2.1.2 Функциональные требования")
    bullets(doc, [
        "Регистрация и аутентификация гостя, вход сотрудников по email и паролю, refresh-сессии и выход.",
        "Публичный каталог типов номеров, поиск доступности по датам и количеству гостей, проверка промокода.",
        "Оформление брони с созданием гостя, проверкой доступности, расчётом стоимости и онлайн-оплатой.",
        "Личный кабинет гостя: предстоящие и прошлые брони, детали, счета, заказ услуг, отмена.",
        "Рабочее место менеджера: дашборд, шахматка, реестр броней, карточка брони, заселение, выселение, перенос.",
        "Folio и платежи: начисления, оплаты, возвраты, закрытие счёта, PDF-счёт, импорт банковской выписки.",
        "Хаускипинг: канбан заданий, старт/завершение/отмена, списание расходников, заявки на ремонт.",
        "Администрирование: пользователи, роли, матрица прав, справочники, аудит, резервные копии, мониторинг, настройки.",
        "Отчёты: загрузка, ADR/RevPAR, отмены/no-show, статусы номеров, расходники, экспорт CSV/PNG.",
        "Пользовательские настройки: тема, язык, формат даты и чисел, размер страниц, сохранённые фильтры.",
    ])
    h3(doc, "2.1.3 Нефункциональные требования")
    table(doc, ["Требование", "Значение / реализация"], [
        ["Производительность", "Публичные запросы — p95 не более 150 мс при 20 параллельных запросах; отчёты — до 2 с на демо-данных"],
        ["Безопасность", "RBAC, bcrypt, JWT, серверная валидация, параметризованные запросы, аудит"],
        ["Надёжность", "Транзакции, откаты, exclusion-ограничение, резервное копирование и restore"],
        ["Совместимость", "Современные Chromium/Firefox/Safari, адаптивность от 390 до 1440 px"],
        ["Локализация", "RU/EN, две темы, форматы даты и чисел"],
        ["Сопровождение", "Docker Compose, README, OpenAPI, тесты, отдельные тексты программы"],
    ], widths=[4.5, 11.0])
    h3(doc, "2.1.4 Тесты на уровне требований")
    table(doc, ["Требование", "Проверка"], [
        ["Запрет двойного бронирования", "Параллельные запросы на один номер и даты; второй запрос отклоняется"],
        ["Заселение только по подтверждённой брони", "Попытка check-in для NEW/CANCELLED отклоняется"],
        ["Контроль остатков расходников", "Списание больше остатка отклоняется триггером"],
        ["Запрет изменений закрытого дня", "Попытка изменить folio закрытого дня отклоняется"],
        ["Разграничение прав", "Гость не получает доступ к manager/admin API, менеджер — к admin"],
        ["Аудит", "Изменение брони создаёт запись в audit_log с пользователем и IP"],
        ["Восстановление", "Резервная копия восстанавливается в отдельную БД, данные целостны"],
    ], widths=[7.0, 8.5])

    h3(doc, "2.1.5 Диаграмма прецедентов")
    p(doc, "Диаграмма прецедентов отражает пять ролей системы и их основные сценарии взаимодействия с SunStay. Гость работает с поиском, бронированием, оплатой, своими бронями, счетами и услугами. Менеджер выполняет подтверждение и отмену броней, заселение и выселение, ведение folio, платежи, ночной аудит, работу с шахматкой и отчётами. Хаускипинг управляет заданиями, статусами номеров, расходниками и заявками на ремонт. Управляющий отелем дополнительно управляет тарифами, услугами, номерным фондом, сотрудниками и аудитом. Администратор БД отвечает за пользователей, роли, справочники, резервное копирование, мониторинг и настройки.")
    figure(doc, DIAGRAMS / "usecase.png", "Диаграмма прецедентов SunStay", width_cm=13.5)
    p(doc, "Диаграмма используется как основа для матрицы прав доступа и для проверки полноты реализованных сценариев: каждому прецеденту соответствуют серверные эндпоинты, проверки RBAC и, при необходимости, записи аудита.")

    h2(doc, "2.2 Проектирование базы данных")
    h3(doc, "2.2.1 ER-диаграмма")
    p(doc, "На концептуальном уровне выделены сущности гостей, номеров, типов номеров, тарифов, бронирований, услуг, folio, платежей, возвратов, заданий хаускипинга, расходников, заявок на ремонт, пользователей и аудита. Связи имеют типы 1:M и M:M; связь «номер — удобство» реализована через таблицу room_amenities.")
    figure(doc, DIAGRAMS / "erd.png", "Концептуальная ER-диаграмма SunStay")
    p(doc, "Полная даталогическая модель из 37 таблиц представлена в файле hotel_sunstay_erd.drawio и в скрипте database/init/001_hotel_db.sql. На диаграмме отражены первичные и внешние ключи, обязательность связей и уровни зависимости таблиц; миграции 008–011 добавляют поля безопасности, шифрования, удержания брони и справочник причин блокировки.")
    h3(doc, "2.2.2 Словарь данных")
    p(doc, "Ниже приведён фрагмент словаря данных по ключевым сущностям. Полный словарь соответствует структуре БД и ERD.")
    table(doc, ["Таблица", "Ключевые поля", "Назначение"], [
        ["guests", "guest_id, full_name, document_number_enc / masked / hash, phone_enc / masked / hash, email, pdn_consent, user_id", "Гости; контакты и документ шифруются, для поиска хранится хэш"],
        ["users", "user_id, role_id, full_name, email, password_hash, is_active, last_seen_at, locked_until, failed_login_attempts, block_reason, blocked_at, blocked_by, phone_enc / masked / hash", "Учётные записи; онлайн-статус, блокировка и защита входа"],
        ["roles", "role_id, name", "Справочник ролей"],
        ["permissions", "permission_id, code, module", "Права доступа"],
        ["role_permissions", "role_id, permission_id", "Связь ролей и прав"],
        ["rooms", "room_id, room_type_id, status_id, room_number, floor", "Номерной фонд"],
        ["room_types", "room_type_id, name, capacity", "Категории номеров"],
        ["rate_plans", "rate_id, room_type_id, season_start, season_end, price_per_night", "Тарифы"],
        ["bookings", "booking_id, guest_id, room_id, rate_id, checkin_date, checkout_date, arrival_time, hold_minutes, hold_until, status", "Бронирования; время заезда и удержание номера"],
        ["check_ins / check_outs", "booking_id, manager_id, actual_checkin_at / actual_checkout_at", "Факты заезда и выезда"],
        ["folios", "folio_id, booking_id, status, opened_at, closed_at", "Лицевые счета"],
        ["folio_lines", "line_id, folio_id, description, amount, line_type, charge_date", "Начисления"],
        ["payments", "payment_id, folio_id, amount, method, payment_type, external_ref", "Платежи"],
        ["refunds", "refund_id, payment_id, amount, reason", "Возвраты"],
        ["services / service_orders", "service_id, name, price / order_id, booking_id, quantity", "Дополнительные услуги"],
        ["housekeeping_tasks", "task_id, room_id, staff_id, task_type, status, priority", "Задания на уборку"],
        ["consumables / consumable_usage", "consumable_id, stock_quantity, min_stock / usage_id, task_id, quantity", "Расходники"],
        ["maintenance_requests", "request_id, room_id, description, priority, status", "Заявки на ремонт"],
        ["audit_log", "log_id, user_id, table_name, record_id, action, old_value, new_value, event_type, severity, is_error, error_message, request_id", "Журнал аудита и событий безопасности"],
        ["user_settings", "user_id, theme, language, date_format, number_format, page_size, saved_filters", "Настройки пользователя"],
        ["user_block_reasons", "reason_id, name", "Справочник причин блокировки учётных записей"],
    ], widths=[4.0, 7.5, 4.0])
    h3(doc, "2.2.3 Нормализация до 3НФ")
    p(doc, "Все таблицы приведены к третьей нормальной форме. В первой нормальной форме атомарные значения полей: например, удобства номера вынесены в отдельную таблицу amenities и связь room_amenities, а не хранятся строкой в rooms. Во второй нормальной форме неключевые поля зависят от полного первичного ключа: в составных связях room_amenities и role_permissions нет частичной зависимости. В третьей нормальной форме устранены транзитивные зависимости: название типа номера хранится в room_types, а не дублируется в rooms; название тарифа — в rate_plans, а не в bookings; способ оплаты и тип платежа вынесены в атрибуты payments.")
    p(doc, "Справочники (роли, типы номеров, статусы, причины блокировки, причины отмены, единицы измерения) отделены от операционных таблиц. Это уменьшает дублирование, упрощает изменение справочных данных и снижает риск аномалий вставки, обновления и удаления.")
    h3(doc, "2.2.4 Структурная схема БД и ограничения")
    p(doc, "База данных включает 37 таблиц, 14 представлений, индексы по внешним ключам и ограничения целостности. Первичные ключи реализованы через GENERATED ALWAYS AS IDENTITY. Внешние ключи используют ON DELETE RESTRICT, CASCADE или SET NULL в зависимости от бизнес-смысла связи.")
    bullets(doc, [
        "UNIQUE: email пользователя, номер комнаты, хэш документа гостя, код промокода, пара room_id + amenity_id.",
        "CHECK: положительная вместимость номера, цена больше нуля, дата выезда позже даты заезда, допустимые статусы и способы оплаты.",
        "EXCLUDE USING gist: запрет пересечения активных броней одного номера на пересекающиеся даты.",
        "Уникальность check-in/check-out по брони и один открытый folio на бронь.",
        "Индексы по внешним ключам и датам бронирования для ускорения JOIN и выборок.",
        "Шифрование контактов и документов: колонки *_enc (Fernet), *_masked (безопасный вывод) и *_hash (поиск и уникальность).",
        "Триггеры аудита, валидации, контроля остатков, удержания брони и закрытых бизнес-дней.",
    ])
    h3(doc, "2.2.5 Представления и отчётные модели")
    p(doc, "Для отчётности созданы представления, инкапсулирующие расчёты и упрощающие API. Основные представления: v_rooms_status, v_booking_summary, v_folio_balance, v_occupancy_daily, v_occupancy_by_type, v_adr_revpar_daily, v_cancellations_monthly, v_cancellation_reasons, v_room_status_today, v_consumables_stock, v_revenue_by_service, v_payments_by_method и v_dashboard_today.")
    p(doc, "Представления не хранят данные, а рассчитываются на основе актуальных таблиц. Для отчётов по загрузке и ADR/RevPAR используется ожидаемая выручка по активным броням, что позволяет корректно строить графики даже до закрытия бизнес-дня. Фактические платежи и начисления при этом остаются в folio и payments.")

    h2(doc, "2.3 Архитектура приложения")
    h3(doc, "2.3.1 Схема архитектуры")
    p(doc, "Архитектура построена по принципу «тонкий клиент — защищённый сервер — централизованная БД». React SPA раздаётся Nginx, который также проксирует запросы к core API и analytics API. Core API отвечает за бизнес-операции и RBAC, analytics API — за отчётность и использует отдельную роль СУБД с доступом только на чтение.")
    figure(doc, DIAGRAMS / "architecture.png", "Архитектурная схема системы SunStay")
    h3(doc, "2.3.2 Микросервисы: core и analytics")
    p(doc, "Core API реализует аутентификацию, бронирования, заселение/выселение, folio, платежи, хаускипинг, администрирование и импорт/экспорт. Analytics API предоставляет эндпоинты отчётов и не изменяет данные. Такое разделение позволяет независимо масштабировать отчётность и снижает риск влияния тяжёлых аналитических запросов на операционные операции.")
    p(doc, "Оба сервиса публикуют OpenAPI-спецификацию. Взаимодействие с фронтендом идёт по REST/JSON; аутентификация — по Bearer JWT. Для аналитики проверяется роль пользователя, для core API — конкретное право доступа.")
    h3(doc, "2.3.3 Схема интерфейсов и навигации")
    p(doc, "Интерфейс разделён на публичную часть и ролевые рабочие области. Гость видит главную страницу, поиск, оформление брони, личный кабинет, брони, счёта, услуги и профиль. Менеджер — дашборд, шахматку, бронирования, folio и платежи, хаускипинг и отчёты. Хаускипинг — задания, заявки и расходники. Управляющий отелем — отчёты, справочники, сотрудники и аудит. Администратор БД — пользователей, справочники, аудит, бэкапы, мониторинг и настройки.")
    figure(doc, DIAGRAMS / "uimap.png", "Карта интерфейсов и ролей")
    h3(doc, "2.3.4 Схема тестирования")
    p(doc, "Тестирование построено по пирамиде: в основании — SQL-тесты процедур, триггеров и ограничений, выше — функциональные тесты API, интеграционные тесты API + БД, нагрузочные и security-тесты, на вершине — E2E и приёмочные сценарии. Для автоматизации используются pytest и psql; для нагрузки — асинхронный httpx-скрипт; для проверки восстановления — отдельная тестовая БД.")
    figure(doc, DIAGRAMS / "testpyramid.png", "Схема тестирования SunStay")

    h2(doc, "2.4 Расширенная серверная логика")
    h3(doc, "2.4.1 Хранимые процедуры и функции")
    p(doc, "Бизнес-операции вынесены на уровень PostgreSQL. Это обеспечивает атомарность, повторное использование логики и независимость от клиента. Основные функции и процедуры приведены в таблице.")
    table(doc, ["Объект", "Тип", "Назначение"], [
        ["fn_room_available", "функция", "Проверка доступности номера на диапазон дат"],
        ["fn_calculate_stay_price", "функция", "Расчёт стоимости проживания с учётом промокода"],
        ["fn_folio_charged / fn_folio_paid / fn_folio_balance", "функции", "Баланс folio"],
        ["fn_create_booking", "функция", "Создание брони с проверкой доступности, ПДн, временем заезда и удержанием"],
        ["sp_confirm_booking", "процедура", "Подтверждение брони"],
        ["sp_cancel_booking", "процедура", "Отмена брони с причиной"],
        ["sp_check_in / sp_check_in_secure", "процедуры", "Заселение, проверка документа по хэшу, открытие folio, депозит"],
        ["sp_check_out", "процедура", "Начисление оставшихся ночей, закрытие folio, задание хаускипингу"],
        ["sp_night_audit", "процедура", "Начисление проживания, no-show, закрытие бизнес-дня; запрет будущих дат"],
        ["fn_add_service_order", "функция", "Заказ услуги и строка folio одной транзакцией"],
        ["fn_record_payment / fn_refund_payment", "функции", "Платёж и возврат с контролем суммы"],
        ["fn_assign_housekeeping_task", "функция", "Создание задания на уборку"],
        ["sp_start_housekeeping_task / sp_complete_housekeeping_task", "процедуры", "Старт и завершение задания"],
        ["fn_write_off_consumable", "функция", "Списание расходника с контролем остатка"],
        ["fn_create_maintenance_request", "функция", "Создание заявки на ремонт"],
        ["sp_set_room_status", "процедура", "Смена статуса номера с проверкой причины блокировки"],
    ], widths=[6.5, 2.5, 6.5])
    h3(doc, "2.4.2 Триггеры")
    table(doc, ["Триггер", "Таблица", "Назначение"], [
        ["trg_validate_booking", "bookings", "Проверка дат, соответствия тарифа типу номера, вместимости, сезона и промокода"],
        ["trg_audit_*", "bookings, rooms, users, folios, payments, refunds, rate_plans, services, guests, housekeeping_tasks, maintenance_requests, consumables", "Запись изменений и ошибок в audit_log; маскирование секретов"],
        ["trg_consumable_stock", "consumable_usage", "Списание и восстановление остатков, запрет отрицательного остатка"],
        ["trg_prevent_closed_day_*", "folio_lines, payments, refunds", "Запрет изменений закрытого бизнес-дня; платежи после закрытия разрешены"],
        ["trg_maintenance_updated_at", "maintenance_requests", "Автоматическое обновление updated_at"],
    ], widths=[5.0, 5.0, 5.5])
    h3(doc, "2.4.3 Транзакции и обработка ошибок")
    p(doc, "Все бизнес-операции выполняются в транзакциях. Создание брони включает проверку доступности и вставку записи; при нарушении exclusion-ограничения транзакция откатывается, а API возвращает понятное сообщение. Заказ услуги и начисление в folio выполняются одной транзакцией: если одна часть не выполнена, вторая также отменяется. Ночной аудит обрабатывает все активные брони и закрывает бизнес-день; при ошибке на любом шаге изменения откатываются полностью.")
    p(doc, "Обработка ошибок реализована на трёх уровнях: ограничения и триггеры PostgreSQL, исключения в хранимых процедурах и централизованная обработка ошибок в FastAPI. Клиент получает HTTP-статус и человекочитаемое сообщение, а технические детали не раскрываются. Ошибки бизнес-операций дополнительно фиксируются в audit_log с признаком is_error и текстом ошибки, чтобы администратор видел их в журнале.")
    p(doc, "Для броней с удержанием номера работает фоновый планировщик: раз в минуту он отменяет брони в статусах NEW и CONFIRMED, у которых hold_until меньше текущего времени, и указывает причину «Истекло время ожидания». Старые брони без hold_until не затрагиваются. Планировщик также проверяет расписание резервного копирования и запускает его в заданное администратором время.")
    h3(doc, "2.4.4 Серверная валидация")
    p(doc, "Валидация выполняется на сервере, а не только в интерфейсе. Проверяются обязательные поля, форматы email и телефона, даты, вместимость номера, соответствие тарифа типу номера, срок действия промокода, остаток расходников, права пользователя и статусные переходы. Для платёжных и финансовых операций дополнительно контролируются суммы и баланс folio. При заселении документ сверяется по SHA-256 хэшу, поэтому открытый номер документа не требуется. При создании брони проверяются время заезда и допустимый интервал удержания, а планировщик отменяет просроченные брони.")

    h2(doc, "2.5 Механизмы защиты и администрирование")
    h3(doc, "2.5.1 RBAC и матрица прав")
    p(doc, "Ролевая модель включает пять ролей и 43 права. Права сгруппированы по модулям: бронирования, номера, тарифы, услуги, folio, платежи, хаускипинг, отчёты, пользователи, аудит, бэкапы, настройки. Матрица «роль × право» хранится в role_permissions и проверяется зависимостями FastAPI.")
    table(doc, ["Модуль", "Гость", "Менеджер", "Хаускипинг", "Управляющий", "Админ БД"], [
        ["Бронирования", "создание, просмотр своих, отмена", "все операции", "—", "все операции", "все операции"],
        ["Номера", "просмотр доступности", "просмотр, статусы", "просмотр, статусы", "управление", "управление"],
        ["Folio/платежи", "просмотр своих", "управление, платежи, возвраты", "—", "управление", "управление"],
        ["Хаускипинг", "—", "просмотр, управление", "просмотр, управление", "просмотр, управление", "просмотр, управление"],
        ["Отчёты", "—", "просмотр, экспорт", "—", "просмотр, экспорт", "просмотр, экспорт"],
        ["Пользователи/права", "—", "—", "—", "сотрудники, назначение ролей", "полный доступ"],
        ["Аудит/бэкапы", "—", "—", "—", "аудит (чтение)", "полный доступ"],
    ], widths=[3.1, 2.8, 3.2, 2.8, 3.0, 2.6])
    h3(doc, "2.5.2 Хэширование паролей и JWT-сессии")
    p(doc, "Пароли хранятся только в виде bcrypt-хэша с солью. При входе сервер сравнивает введённый пароль с хэшем и не передаёт пароль в открытом виде. Для всех ролей действует единое правило: после трёх неудачных попыток подряд учётная запись блокируется на 30 секунд. Счётчик сбрасывается после успешного входа и после истечения блокировки. События LOGIN_SUCCESS, LOGIN_FAILED и LOGIN_BLOCKED фиксируются в audit_log с IP-адресом и Request ID.")
    p(doc, "Аутентификация построена на JWT: access-токен живёт ограниченное время, refresh-токен хранится в user_sessions в виде SHA-256 хэша. При выходе refresh-сессия отзывается. Пароли и секреты не хранятся в репозитории, конфигурация передаётся через переменные окружения.")
    h3(doc, "2.5.3 Аудит")
    p(doc, "Журнал audit_log фиксирует пользователя, таблицу, идентификатор записи, действие, старое и новое значение, время, IP-адрес, User-Agent и Request ID. Дополнительно хранятся event_type, severity, is_error и error_message. Записи создаются триггерами на ключевых таблицах, поэтому аудит не зависит от того, вызвано действие через API или напрямую через БД; пароли, хэши и зашифрованные значения в снимки не попадают.")
    p(doc, "Интерфейс аудита разделён на вкладки «Изменения данных», «Пользователи и вход» и «Системные события». Ошибки выделяются красным, доступны фильтры по роли, пользователю, таблице, действию, признаку ошибки и датам, а также экспорт CSV. Это позволяет быстро найти неудачные входы, заблокированные попытки и ошибки бронирования.")
    h3(doc, "2.5.4 Резервное копирование и восстановление")
    p(doc, "Резервное копирование выполняется утилитой pg_dump в формате custom (.dump). Используется одна актуальная копия sunstay_latest.dump: каждый запуск перезаписывает файл, поэтому не требуется следить за сроком хранения и диском. Скрипты backup.ps1 и restore.ps1 автоматизируют создание и восстановление; для проверки восстановление выполняется в отдельную базу hotel_restore_test с последующей сверкой количества таблиц и броней.")
    p(doc, "Администратор БД может создать копию, скачать её и восстановить базу из админ-панели, а также задать время ежедневного запуска. Расписание, статус, время последнего запуска и текст ошибки хранятся в system_settings. Фоновый планировщик проверяет настройки и запускает backup в заданное время; файл хранится в каталоге /backups, подключённом как volume. На экране бэкапов дополнительно показаны размер БД, активные соединения и телеметрия таблиц.")
    h3(doc, "2.5.5 Защита ПДн и секретов")
    p(doc, "Для гостей хранится согласие на обработку персональных данных. Телефоны и номера документов гостей и сотрудников шифруются на уровне приложения алгоритмом Fernet (AES-128-CBC + HMAC-SHA256) ключом DATA_ENCRYPTION_KEY из переменных окружения. В БД хранятся три колонки: *_enc (шифртекст), *_masked (безопасное представление для интерфейса) и *_hash (SHA-256 для поиска и уникальности). Открытые значения контактов не возвращаются ни одной роли: в API и интерфейсе показываются только маски, email остаётся открытым для связи. При заселении документ сверяется по хэшу, поэтому менеджеру не нужен открытый номер документа.")
    p(doc, "Персональные данные не выводятся в журналах и аудите: триггер аудита исключает поля *_enc, *_hash и password_hash. Секреты (пароль БД, JWT-секрет, ключ шифрования) передаются через переменные окружения и не коммитятся в Git. SQL-запросы параметризованы, что снижает риск SQL-инъекций.")

    h2(doc, "2.6 Клиент-серверное приложение и API")
    h3(doc, "2.6.1 REST API и OpenAPI")
    p(doc, "Core API предоставляет REST-эндпоинты для аутентификации, публичного каталога, гостя, менеджера, хаускипинга, администратора и импорта. Analytics API предоставляет отчёты. Оба сервиса публикуют OpenAPI-спецификацию по адресам /api/docs и /api/openapi.json.")
    table(doc, ["Группа", "Примеры эндпоинтов"], [
        ["Auth", "POST /api/auth/login, POST /api/auth/refresh, POST /api/auth/register, GET /api/auth/me"],
        ["Public", "GET /api/public/room-types, GET /api/public/availability, POST /api/public/bookings"],
        ["Guest", "GET /api/guest/bookings, GET /api/guest/folios, POST /api/guest/bookings/{id}/services"],
        ["Manager", "GET /api/manager/dashboard, GET /api/manager/room-grid, POST /api/manager/bookings/{id}/check-in"],
        ["Folio", "GET /api/manager/folios, POST /api/manager/folios/{id}/payments, POST /api/manager/payments/{id}/refunds"],
        ["Housekeeping", "GET /api/housekeeping/tasks, POST /api/housekeeping/tasks/{id}/complete"],
        ["Admin", "GET /api/admin/users/stats, POST /api/admin/users/{id}/block, GET /api/admin/audit, POST /api/admin/backups, POST /api/admin/backups/restore"],
        ["Reports", "GET /api/reports/occupancy, GET /api/reports/adr-revpar, GET /api/reports/cancellations"],
        ["Imports", "POST /api/imports/bank-statement/preview, POST /api/imports/rates/commit"],
    ], widths=[3.5, 12.0])
    h3(doc, "2.6.2 Импорт и экспорт")
    p(doc, "Импорт банковской выписки принимает CSV с колонками date, amount, method, booking_id или folio_id, external_ref. Сначала выполняется предпросмотр: проверяются даты, суммы, способ оплаты, существование folio, статус счёта и дубликаты external_ref. Пользователь видит отчёт об ошибках и только затем подтверждает загрузку. Импорт тарифов принимает CSV с типом номера, названием, периодом и ценой; также используется предпросмотр.")
    p(doc, "Экспорт реализован для реестров бронирований, аудита, отчётов (CSV), счетов (PDF) и визуализаций (PNG). CSV формируется с BOM и разделителем «;», чтобы корректно открываться в Excel.")
    h3(doc, "2.6.3 Пользовательские настройки, темы, RU/EN, хоткеи")
    p(doc, "Настройки пользователя хранятся на сервере в user_settings: тема, язык, формат даты, формат чисел, размер страницы и сохранённые фильтры. При входе настройки применяются автоматически. Поддерживаются светлая, тёмная и системная темы; все экраны используют единые дизайн-токены.")
    p(doc, "Интерфейс поддерживает русский и английский языки. Для частых операций реализованы горячие клавиши: ?, N, F, G, B, R, T, L, Esc, Ctrl+Enter. Список горячих клавиш доступен из профиля и из верхней панели.")

    h2(doc, "2.7 Подсистема статистики и отчётности")
    h3(doc, "2.7.1 Метрики и формулы")
    table(doc, ["Метрика", "Формула", "Смысл"], [
        ["Occupancy", "Занятые номеро-ночи / доступные номеро-ночи × 100%", "Загрузка номерного фонда"],
        ["ADR", "Выручка от проживания / проданные номеро-ночи", "Средняя цена проданного номера"],
        ["RevPAR", "Выручка от проживания / доступные номеро-ночи", "Доход на доступный номер"],
        ["Cancellation rate", "Отменённые брони / все брони × 100%", "Доля отмен"],
        ["No-show rate", "Неявки / все брони × 100%", "Доля неявок"],
        ["Room revenue", "Сумма стоимости проживания по активным броням", "Выручка от номерного фонда"],
    ], widths=[3.5, 7.0, 5.0])
    h3(doc, "2.7.2 Отчётные представления")
    p(doc, "Отчётные представления рассчитывают показатели по дням, типам номеров и месяцам. v_occupancy_daily и v_occupancy_by_type показывают загрузку, v_adr_revpar_daily — ADR и RevPAR, v_cancellations_monthly и v_cancellation_reasons — отмены и no-show, v_room_status_today — текущие статусы номеров, v_consumables_stock — остатки и расход материалов, v_revenue_by_service — выручку по услугам, v_payments_by_method — платежи по способам.")
    h3(doc, "2.7.3 Визуализации")
    p(doc, "На экране отчётов доступны пять вкладок: «Загрузка», «ADR и RevPAR», «Отмены и no-show», «Статусы номеров», «Расходники». Используются area, line, bar и donut-диаграммы, KPI-карточки и таблицы. Фильтры позволяют выбрать период и тип номера, сохранить фильтр, экспортировать данные в CSV и снимок экрана в PNG.")
    p(doc, "На дашборде менеджера график загрузки показывает последние семь календарных дней, а не весь диапазон данных, поэтому не образует пустого белого блока. Шахматка отображает брони цветными точками без имён гостей: янтарный — новая, зелёный — подтверждена, голубой — заселён, серый — выселен, красный — отменена. Это снижает риск раскрытия персональных данных при демонстрации экрана.")

    h2(doc, "2.8 Результаты работы программы")
    p(doc, "Ниже приведены основные экраны разработанной системы. Интерфейс выполнен в едином стиле, поддерживает светлую и тёмную темы, русский и английский языки, адаптивную вёрстку.")
    figure(doc, SHOTS / "landing.png", "Главная страница публичного сайта")
    p(doc, "На главной странице расположены поиск доступности, карточки категорий номеров, промокод и преимущества отеля. Поиск передаёт даты и количество гостей в API и открывает страницу результатов.")
    figure(doc, SHOTS / "login.png", "Страница входа и демо-доступа")
    p(doc, "Страница входа содержит вкладки входа и регистрации, а также демо-аккаунты пяти ролей. Пароли демо-аккаунтов предназначены только для учебного стенда.")
    figure(doc, SHOTS / "manager-dashboard.png", "Дашборд менеджера")
    p(doc, "Дашборд показывает загрузку, ADR, RevPAR, выручку, заезды, выезды и статусы номеров. Данные берутся из представлений PostgreSQL и обновляются по запросу. График загрузки компактный и показывает последние семь дней, статусы номеров вынесены в отдельную donut-диаграмму.")
    figure(doc, SHOTS / "room-grid.png", "Шахматка номеров")
    p(doc, "Шахматка отображает брони по номерам и датам цветными точками без имён гостей и деталей брони. Свободная ячейка открывает форму создания брони, точка — карточку брони. Фильтры позволяют выбрать этаж и статус номера.")
    figure(doc, SHOTS / "bookings-registry.png", "Реестр бронирований")
    p(doc, "Реестр поддерживает поиск, фильтры по датам и статусам, пагинацию, массовые операции, сохранённые фильтры и экспорт CSV.")
    figure(doc, SHOTS / "folio-payments.png", "Folio и платежи")
    p(doc, "Экран folio показывает начисления, платежи, возвраты и баланс. Доступны добавление платежа, возврат, закрытие счёта, PDF-счёт и импорт банковской выписки.")
    figure(doc, SHOTS / "reports.png", "Отчёты и аналитика")
    p(doc, "Отчёты содержат KPI, графики и таблицы. На скриншоте показана динамика загрузки за период; вкладки переключают ADR/RevPAR, отмены, статусы номеров и расходники.")
    figure(doc, SHOTS / "housekeeping.png", "Доска хаускипинга")
    p(doc, "Канбан-доска группирует задания по статусам. Карточка задания показывает номер, тип, приоритет, исполнителя и статус номера; при завершении задания номер переводится в статус «Готов».")
    figure(doc, SHOTS / "guest-dashboard.png", "Личный кабинет гостя")
    p(doc, "Гость видит ближайшую поездку, историю броней, баланс последнего счёта и рекомендованные услуги. Навигация ограничена гостевой рабочей областью.")
    figure(doc, SHOTS / "guest-bookings.png", "Мои бронирования")
    p(doc, "Список броней разделён на предстоящие, историю и отменённые. Гость может открыть детали, скачать счёт или отменить бронь с указанием причины.")
    figure(doc, SHOTS / "admin-users.png", "Пользователи, роли и матрица прав")
    p(doc, "Администратор БД видит KPI-карточки «Всего / Онлайн / Активные / Заблокированные», фильтры по роли и статусу, маскированные контакты и признак онлайн. Блокировка выполняется с выбором причины из справочника или вводом своей; причина и автор блокировки сохраняются, активные сессии отзываются. Матрица полномочий позволяет включать и отключать права для выбранной роли.")
    figure(doc, SHOTS / "admin-directories.png", "Справочники отеля")
    p(doc, "Справочники объединяют типы номеров, номера, удобства, тарифы, услуги, промокоды и причины отмены. Для тарифов доступен импорт CSV с предпросмотром.")
    figure(doc, SHOTS / "admin-audit.png", "Журнал аудита — изменения данных")
    p(doc, "Журнал аудита разделён на вкладки «Изменения данных», «Пользователи и вход» и «Системные события». Ошибки выделяются красным, доступны фильтры по роли, пользователю, таблице, действию, признаку ошибки и датам, diff «Было / Стало» и экспорт CSV.")
    figure(doc, SHOTS / "admin-audit-login.png", "Журнал аудита — события входа и ошибки")
    p(doc, "На вкладке «Пользователи и вход» видны успешные входы, неудачные попытки и блокировки с IP-адресом, пользователем и ролью. Неудачные попытки и блокировки выделены красным, что позволяет быстро обнаружить перебор пароля.")
    figure(doc, SHOTS / "admin-backups.png", "Резервное копирование и мониторинг")
    p(doc, "Администратор БД видит одну актуальную копию sunstay_latest.dump, её размер и время обновления, может скачать копию, создать новую и восстановить базу. Здесь же задаётся время ежедневного запуска и отображается статус последней копии, размер БД, активные соединения и телеметрия таблиц.")
    figure(doc, SHOTS / "manager-dashboard-dark.png", "Тёмная тема интерфейса")
    p(doc, "Тёмная тема использует те же компоненты и сетку, что и светлая. Переключение темы не меняет структуру экранов и доступные действия.")
    p(doc, "Результаты нагрузочного теста:")
    table(doc, ["Сценарий", "Запросов", "Параллельно", "RPS", "Среднее, мс", "p95, мс", "Ошибки"], [
        ["GET /api/public/room-types", "200", "20", "264,40", "67,11", "111,29", "0"],
        ["GET /api/public/availability", "100", "10", "284,07", "34,02", "66,49", "0"],
    ], widths=[5.8, 2.0, 2.3, 2.0, 2.2, 2.0, 1.7])
    p(doc, "SQL-тесты: 14 проверок (доступность, цена, создание брони, подтверждение, заселение, услуги, платежи, возвраты, ночной аудит, выселение, остатки, аудит, шифрование, безопасное заселение, будущий и закрытый бизнес-день) — успешно. API-тесты: 12 проверок (health, дашборд, доступность, RBAC, отчёты, PDF, SQL-инъекция, админ, статистика пользователей, аудит входов, маскирование контактов, бэкапы) — успешно.")

    # ------------------------------------------------------------------ 3 ТЕХНОЛОГИЧЕСКАЯ ЧАСТЬ
    h1(doc, "3 ТЕХНОЛОГИЧЕСКАЯ ЧАСТЬ")
    h2(doc, "3.1 Используемые языки, СУБД, фреймворки")
    p(doc, "Серверная часть реализована на Python 3.13 с использованием FastAPI. FastAPI выбран за автоматическую генерацию OpenAPI, строгую валидацию Pydantic и удобную систему зависимостей для RBAC. Для работы с PostgreSQL используется psycopg 3 с асинхронным пулом соединений. Пароли хэшируются bcrypt, токены подписываются PyJWT, чувствительные контакты шифруются библиотекой cryptography (Fernet), фоновые задачи выполняются асинхронными планировщиками.")
    p(doc, "Клиентская часть реализована на React 18 и TypeScript. Vite обеспечивает быструю сборку, Tailwind CSS — единые дизайн-токены и адаптивность, Recharts — визуализацию отчётов. Состояние данных управляется TanStack Query, маршрутизация — React Router.")
    p(doc, "PostgreSQL 16 выбран как надёжная объектно-реляционная СУБД с поддержкой транзакций, exclusion-ограничений, хранимых процедур, триггеров и оконных функций. Docker Compose обеспечивает воспроизводимое окружение и упрощает перенос на сервер.")
    h2(doc, "3.2 Процесс разработки и отладки")
    p(doc, "Разработка велась итеративно по неделям: анализ и БД, серверная логика, безопасность, API и интерфейс, отчётность, тестирование. Изменения фиксировались в Git; для проверки использовались psql, pytest, tsc, vite build, DevTools браузера и логи контейнеров.")
    p(doc, "Отладка API выполнялась через Swagger UI, логи uvicorn и psql. Ошибки БД анализировались по тексту исключений PostgreSQL и планам выполнения. На фронтенде использовались React DevTools, Network Panel и консоль браузера. Для проверки адаптивности применялись Playwright и скриншоты в разных разрешениях.")
    h2(doc, "3.3 Защитное программирование")
    p(doc, "В коде применяются проверка типов Pydantic, обработка исключений, транзакции и повторная серверная валидация. Все SQL-запросы параметризованы. Для опасных операций (восстановление БД, изменения прав) требуется отдельное право и подтверждение. Ошибки не раскрывают внутренние детали; пользователь получает понятное сообщение, а техническая информация пишется в лог.")
    p(doc, "Идемпотентность достигается за счёт уникальных ограничений, проверки существования записей и запрета повторного ночного аудита закрытого дня. Миграция шифрования при повторном запуске пропускает уже обработанные записи и не шифрует маски повторно. Для финансовых операций контролируется остаток платежа при возврате. Для расходников триггер не позволяет уйти в отрицательный остаток. Планировщик удержаний отменяет только брони с истёкшим hold_until и не трогает старые записи с NULL.")
    h2(doc, "3.4 DevOps-схема")
    p(doc, "Проект разворачивается через Docker Compose. Сервисы db, api, analytics, web и adminer связаны внутренней сетью. Nginx раздаёт статику и проксирует /api и /analytics. Переменные окружения задаются в .env; секреты не хранятся в репозитории. Резервные копии складываются в volume /backups.")
    p(doc, "Для локальной разработки используются Vite dev server и uvicorn. Для production — multi-stage сборка фронтенда и Nginx. При наличии CI/CD возможны автоматические проверки pytest, tsc, vite build и сборка Docker-образов.")
    h2(doc, "3.5 Характеристики системы")
    table(doc, ["Характеристика", "Значение"], [
        ["Тип приложения", "Клиент-серверное веб-приложение"],
        ["СУБД", "PostgreSQL 16"],
        ["Серверные сервисы", "FastAPI core, FastAPI analytics"],
        ["Клиент", "React SPA, адаптивная вёрстка"],
        ["Поддерживаемые браузеры", "Chromium, Firefox, Safari (актуальные версии)"],
        ["Аутентификация", "JWT access/refresh, bcrypt"],
        ["Разграничение прав", "RBAC, 5 ролей, 43 права"],
        ["Отчётность", "5 вкладок, CSV/PNG, PDF-счета"],
        ["Резервное копирование", "pg_dump custom, restore в отдельную БД"],
        ["Локализация", "RU/EN, светлая/тёмная тема"],
        ["Горячие клавиши", "10 комбинаций"],
        ["Минимальные требования к серверу", "2 ГБ ОЗУ, 10 ГБ диска, Docker"],
    ], widths=[6.0, 9.5])

    # ------------------------------------------------------------------ ЗАКЛЮЧЕНИЕ
    h1(doc, "ЗАКЛЮЧЕНИЕ")
    p(doc, "В ходе выполнения курсового проекта разработана клиент-серверная информационная система гостиницы «SunStay», автоматизирующая бронирование, заселение, проживание, выселение, биллинг, хаускипинг, техобслуживание, отчётность и администрирование.")
    p(doc, "Спроектирована реляционная база данных из 37 таблиц, нормализованная до третьей нормальной формы. Реализованы ограничения целостности, exclusion-ограничение против двойного бронирования, индексы, представления, функции, хранимые процедуры и триггеры. Бизнес-операции выполняются атомарно и фиксируются в журнале аудита.")
    p(doc, "Реализована ролевая модель на пять ролей, хэширование паролей bcrypt, JWT access/refresh-сессии, блокировка после трёх неудачных попыток входа на 30 секунд, аудит с IP/User-Agent/Request ID и подсветкой ошибок, шифрование контактов и документов, резервное копирование в один файл по расписанию и восстановление. Разработаны REST API и React SPA с двумя темами, RU/EN, горячими клавишами и сохранёнными фильтрами.")
    p(doc, "Создана подсистема статистики и отчётности: загрузка, ADR/RevPAR, отмены и no-show, статусы номеров, расходники. Отчёты поддерживают фильтры, визуализации и экспорт CSV/PNG. Проведены SQL-, API-, нагрузочные и security-тесты, а также тест восстановления базы данных.")
    p(doc, "Результаты работы соответствуют поставленным цели и задачам. Система может быть развёрнута в Docker Compose, перенесена на сервер и использована как основа для дальнейшего развития: интеграции с платёжным шлюзом, OTA-каналами, мобильным приложением и расширенной аналитикой.")

    # ------------------------------------------------------------------ ИСТОЧНИКИ
    h1(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ МАТЕРИАЛОВ")
    sources = [
        "ГОСТ 7.32-2017. Отчёт о научно-исследовательской работе. Структура и правила оформления.",
        "ГОСТ 19.101-77. Единая система программной документации. Виды программ и программных документов.",
        "ГОСТ 34.602-89. Техническое задание на создание автоматизированной системы.",
        "ГОСТ Р 7.0.5-2008. Библиографическая ссылка. Общие требования и правила составления.",
        "PostgreSQL 16 Documentation. URL: https://www.postgresql.org/docs/ (дата обращения: 16.11.2026).",
        "FastAPI Documentation. URL: https://fastapi.tiangolo.com/ (дата обращения: 16.11.2026).",
        "psycopg 3 Documentation. URL: https://www.psycopg.org/psycopg3/docs/ (дата обращения: 16.11.2026).",
        "React Documentation. URL: https://react.dev/ (дата обращения: 16.11.2026).",
        "Vite Documentation. URL: https://vite.dev/ (дата обращения: 16.11.2026).",
        "Tailwind CSS Documentation. URL: https://tailwindcss.com/docs (дата обращения: 16.11.2026).",
        "Recharts Documentation. URL: https://recharts.org/ (дата обращения: 16.11.2026).",
        "Docker Compose Documentation. URL: https://docs.docker.com/compose/ (дата обращения: 16.11.2026).",
        "RFC 7519. JSON Web Token (JWT). – 2015.",
        "OWASP Top 10. URL: https://owasp.org/www-project-top-ten/ (дата обращения: 16.11.2026).",
        "Бэнкер К. PostgreSQL 14. Основы языка SQL. – М.: ДМК Пресс, 2022.",
        "Лутц М. Изучаем Python. 5-е изд. – СПб.: Символ-Плюс, 2019.",
    ]
    for index, source in enumerate(sources, 1):
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        run = paragraph.add_run(f"{index}. {source}")
        set_run_font(run, 14)

    # ------------------------------------------------------------------ ПРИЛОЖЕНИЯ
    h1(doc, "ПРИЛОЖЕНИЯ")
    h2(doc, "Приложение А. Техническое задание")
    p(doc, "Техническое задание на проект представлено в файле «Отель_КП (1).docx» в корне проекта. Оно содержит описание предметной области, пяти ролей, бизнес-процессов, требований к интерфейсу, API, отчётности, безопасности и тестированию.")
    h2(doc, "Приложение Б. Ссылка на репозиторий и тексты программы")
    p(doc, "Исходный код размещается в локальном Git-репозитории проекта. После публикации на GitHub/GitLab ссылка добавляется в README.md. Полные тексты программы вынесены в отдельные файлы:")
    bullets(doc, [
        "backend/CODE_SERVER.md — FastAPI core, analytics, Docker Compose, PDF-сервис, API-тесты;",
        "database/CODE_DATABASE.md — все SQL-скрипты, миграции, роли БД, демо-данные и SQL-тесты;",
        "frontend/CODE_FRONTEND.md — React/TypeScript-приложение, дизайн-токены, конфигурация Vite/Tailwind, Nginx.",
    ])
    p(doc, "В пояснительную записку полные листинги не вставляются, чтобы сохранить читаемость основного текста; они доступны в перечисленных файлах.")
    h2(doc, "Приложение В. Тест-план и результаты тестирования")
    table(doc, ["Вид тестирования", "Что проверялось", "Результат"], [
        ["SQL-тесты", "Функции, процедуры, триггеры, ограничения, транзакции, шифрование, hold", "14 проверок, успешно"],
        ["API-тесты", "Health, auth, RBAC, отчёты, PDF, SQL-инъекция, админ, маскирование, бэкапы", "12 тестов, успешно"],
        ["Нагрузочное", "200 запросов room-types, 100 запросов availability", "0 ошибок, p95 111,29 и 66,49 мс"],
        ["Security", "Доступ гостя к manager API, менеджера к admin API, SQL-инъекция, блокировка входа", "Доступ запрещён, инъекция и перебор отклонены"],
        ["Restore", "Восстановление дампа в отдельную БД", "37 таблиц, 42 брони, успешно"],
    ], widths=[3.5, 8.5, 3.5])
    h2(doc, "Приложение Г. Руководство пользователя")
    p(doc, "Для гостя: откройте главную страницу, выберите даты и количество гостей, нажмите «Найти номер», выберите категорию, заполните данные и оплатите бронь. В личном кабинете доступны брони, счета, услуги и профиль.")
    p(doc, "Для менеджера: войдите под демо-аккаунтом менеджера, откройте «Бронирования» или «Шахматку», создайте бронь, подтвердите её, выполните заселение, примите платёж и при выезде закройте folio. Ночной аудит запускается с дашборда.")
    p(doc, "Для хаускипинга: откройте «Доска хаускипинга», начните задание, отметьте выполнение и при необходимости спишите расходники. Для ремонта создайте заявку в разделе «Техзаявки».")
    p(doc, "Для администратора БД: управляйте пользователями и правами, справочниками, просматривайте аудит, создавайте резервные копии и восстанавливайте базу. Настройки системы доступны в разделе «Настройки».")
    h2(doc, "Приложение Д. Скрипты базы данных и дампы")
    p(doc, "Скрипты инициализации, миграции, роли, демо-данные и SQL-тесты вынесены в database/CODE_DATABASE.md. Резервные копии создаются скриптом scripts/backup.ps1 и восстанавливаются scripts/restore.ps1. Проверка restore выполняется scripts/test_backup_restore.ps1.")
    h2(doc, "Приложение Е. Экспортированные отчёты и визуализации")
    p(doc, "Скриншоты интерфейса и диаграммы находятся в каталогах docs/screenshots и docs/diagrams. Результаты нагрузочного теста — в docs/load_test_results.json. Эти материалы могут быть использованы при защите проекта.")

    doc.save(str(OUTPUT))
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    build()
