"""Enrich the finished SunStay DOCX files in place (title page is never touched).

Fixes:
  * every appendix TOC entry becomes a working internal link
  * all tables lose their shading (plain, no fill)
  * full test suite (25 scenarios) in appendix В
  * four testing-scheme diagrams inserted in appendix В
  * module / dictionary / requirements tables and UI screenshots in other appendices
"""
from __future__ import annotations

import copy
import glob
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph
from docx.table import Table

import test_cases

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DIAG = DOCS / "diagrams"
SHOTS = DOCS / "screenshots"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

SODER = "".join(map(chr, [1057, 1086, 1076, 1077, 1088, 1078, 1072, 1085, 1080, 1077]))  # Содержание
PRILOZ = "".join(map(chr, [1055, 1088, 1080, 1083, 1086, 1078, 1077, 1085, 1080, 1077]))  # Приложение

BM_ID = 5000


def norm(s: str) -> str:
    return re.sub(r"[\s\u00a0]+", " ", s.strip()).lower()


def text_of(p: Paragraph) -> str:
    return p.text.strip()


def set_font(run, size=14, bold=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    run.font.underline = False
    rpr = run._r.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    rf.set(qn("w:ascii"), "Times New Roman")
    rf.set(qn("w:hAnsi"), "Times New Roman")
    rf.set(qn("w:cs"), "Times New Roman")


def add_bookmark(p: Paragraph, name: str):
    global BM_ID
    BM_ID += 1
    s = OxmlElement("w:bookmarkStart")
    s.set(qn("w:id"), str(BM_ID)); s.set(qn("w:name"), name)
    e = OxmlElement("w:bookmarkEnd")
    e.set(qn("w:id"), str(BM_ID))
    p._p.insert(0, s)
    p._p.append(e)


def wrap_link(p: Paragraph, anchor: str):
    """Wrap existing runs of a TOC paragraph into an internal hyperlink."""
    if p._p.findall(W + "hyperlink"):
        return  # already linked
    runs = list(p.runs)
    if not runs:
        return
    hl = OxmlElement("w:hyperlink")
    hl.set(qn("w:anchor"), anchor)
    for r in runs:
        r.font.color.rgb = RGBColor(0, 0, 0)
        r.font.underline = False
        hl.append(r._r)
    p._p.append(hl)


def new_para(doc: Document, text: str = "", style: str | None = None,
             align=None, size=14, bold=False) -> Paragraph:
    p = doc.add_paragraph()
    if style:
        try:
            p.style = style
        except KeyError:
            pass
    if align is not None:
        p.alignment = align
    p.paragraph_format.first_line_indent = Cm(0)
    if text:
        set_font(p.add_run(text), size, bold)
    return p


def insert_after(anchor, *nodes):
    cur = anchor._p if hasattr(anchor, "_p") else anchor._tbl if hasattr(anchor, "_tbl") else anchor
    for node in nodes:
        el = node._p if hasattr(node, "_p") else node._tbl if hasattr(node, "_tbl") else node
        cur.addnext(el)
        cur = el


def new_table(doc: Document, headers, rows, widths=None) -> Table:
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        c.paragraphs[0].paragraph_format.first_line_indent = Cm(0)
        set_font(c.paragraphs[0].add_run(str(h)), 11, True)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            c = cells[i]
            c.text = ""
            c.paragraphs[0].paragraph_format.first_line_indent = Cm(0)
            set_font(c.paragraphs[0].add_run(str(v)), 11)
    if widths:
        for r in t.rows:
            for i, width in enumerate(widths):
                r.cells[i].width = Cm(width)
    strip_shading(t)
    return t


def strip_shading(table: Table):
    for el in table._tbl.iter(W + "shd"):
        el.getparent().remove(el)


def new_picture(doc: Document, path: Path, caption: str, width=15.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.add_run().add_picture(str(path), width=Cm(width))
    cap = new_para(doc, caption, align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    return p, cap


def find(doc: Document, pred, start=0):
    for i, p in enumerate(doc.paragraphs):
        if i >= start and pred(text_of(p)):
            return i, p
    return -1, None


def region_bounds(doc: Document, title: str):
    """Return (start_index, end_index) of one appendix inside the full PZ."""
    paras = doc.paragraphs
    s = -1
    # the real appendix title is right-aligned (TOC entries are not)
    for i, p in enumerate(doc.paragraphs):
        if text_of(p).startswith(title) and p.alignment == 2:
            s = i
            break
    if s < 0:
        return None
    e = len(paras)
    for i in range(s + 1, len(paras)):
        if text_of(paras[i]).startswith(PRILOZ + " ") and text_of(paras[i]) != title:
            e = i
            break
        if text_of(paras[i]) == "ПРИЛОЖЕНИЯ":
            e = i
            break
    return s, e


def key_for(label: str) -> str:
    s = label.split("\t")[0].strip()
    s = re.sub(r"^[\d.]+\s*", "", s)
    return norm(s)


def link_appendix_toc(doc: Document, start: int, end: int):
    """Make every TOC entry in one appendix clickable."""
    paras = doc.paragraphs
    toc_idx, _ = find(doc, lambda t: t.lower() == SODER.lower(), start)
    if toc_idx < 0 or toc_idx >= end:
        return 0
    # body candidates in this region, after the TOC heading
    body = [(i, p) for i, p in enumerate(paras)
            if toc_idx < i < end and not p.style.name.startswith(SODER)]
    linked = 0
    for i in range(toc_idx + 1, end):
        p = paras[i]
        if not p.style.name.startswith(SODER):
            continue
        label = text_of(p)
        if not label:
            continue
        key = key_for(label)
        if not key:
            continue
        target = None
        for off in (key, key[:18], key[:12], " ".join(key.split()[:2])):
            if not off:
                continue
            target = next((q for _, q in body if norm(text_of(q)).startswith(off)), None)
            if target is not None:
                break
        if target is None:
            target = body[0][1] if body else None
        if target is None:
            continue
        name = "bm_app_%d" % BM_ID
        add_bookmark(target, name)
        wrap_link(p, name)
        linked += 1
    return linked


def h2_style(doc):
    return "Заголовок 21" if "Заголовок 21" in [s.name for s in doc.styles] else "Heading 2"


def h3_style(doc):
    return "Заголовок 31" if "Заголовок 31" in [s.name for s in doc.styles] else "Heading 3"


# ------------------------------------------------------------------ appendix Б
def enrich_b(doc: Document, s: int, e: int):
    paras = doc.paragraphs
    h2s, h3s = h2_style(doc), h3_style(doc)
    i_nom, p_nom = find(doc, lambda t: t.startswith("Наименование программы"), s)
    i_obl, p_obl = find(doc, lambda t: t.startswith("Область применения программы"), s)
    i_mod, p_mod = find(doc, lambda t: t.startswith("Модули:"), s)
    if i_nom < 0 or i_nom > e:
        return
    head = new_para(doc, "1. ТЕКСТ ПРОГРАММЫ", h2s)
    sub = new_para(doc, "1.1. Наименование программы", h3s)
    p_nom._p.addprevious(head._p)
    head._p.addnext(sub._p)
    if 0 <= i_obl < e:
        p_obl._p.addprevious(new_para(doc, "1.2. Область применения программы", h3s)._p)
    if 0 <= i_mod < e:
        p_mod._p.addprevious(new_para(doc, "1.3. Модули", h3s)._p)
        cap = new_para(doc, "Таблица 1. Модули программного комплекса", size=12, bold=True)
        tbl = new_table(doc,
            ["Модуль", "Назначение"],
            [["backend/app/api/auth.py", "Регистрация, вход, роли и двухфакторная аутентификация"],
             ["backend/app/api/public.py", "Каталог номеров, доступность и отзывы"],
             ["backend/app/api/manager.py", "Брони, заселение, folio, хаускипинг и отчёты"],
             ["backend/app/api/admin.py", "Пользователи, справочники, аудит и бэкапы"],
             ["backend/app/services/backup.py", "Резервное копирование и восстановление БД"],
             ["backend/app/notifications.py", "Уведомления гостям и сотрудникам"],
             ["frontend/src/App.tsx", "Клиентское SPA и маршрутизация по ролям"],
             ["frontend/src/lib/api.ts", "Типизированный клиент REST API"],
             ["database/init/*.sql", "Схема БД, миграции и демонстрационные данные"]],
            widths=[6.5, 9.0])
        insert_after(p_mod, cap, tbl)


# ------------------------------------------------------------------ appendix В
def enrich_v(doc: Document, s: int, e: int):
    paras = doc.paragraphs
    h2s, h3s = h2_style(doc), h3_style(doc)
    i, p_cel = find(doc, lambda t: t.startswith("Цель испытаний"), s)
    if i < 0 or i > e:
        return
    i_obj, p_obj = find(doc, lambda t: t.startswith("Объект испытаний"), s)
    i_sred, p_sred = find(doc, lambda t: t.startswith("Средства испытаний"), s)
    i_met, p_met = find(doc, lambda t: t.startswith("Методы испытаний"), s)

    p_cel._p.addprevious(new_para(doc, "1. ЦЕЛЬ ИСПЫТАНИЙ", h2s)._p)
    if 0 <= i_obj < e:
        p_obj._p.addprevious(new_para(doc, "2. ОБЪЕКТ ИСПЫТАНИЙ", h2s)._p)
        insert_after(p_obj,
            new_para(doc, "2.1. Наименование объекта", h3s),
            new_para(doc, "Наименование — информационная система «SunStay»."),
            new_para(doc, "2.2. Область применения объекта", h3s),
            new_para(doc, "Система предназначена для автоматизации бронирования, заселения, выселения, биллинга, хаускипинга и отчётности гостиницы."),
            new_para(doc, "2.3. Обозначение объекта", h3s),
            new_para(doc, "Обозначение — информационная система «SunStay» (веб-приложение)."))
    if 0 <= i_sred < e:
        nodes = [new_para(doc, "3. ТРЕБОВАНИЯ К ТЕСТИРОВАНИЮ", h2s),
                 new_para(doc, "3.1. Схема тестирования", h3s),
                 new_para(doc, "Тестирование разработанного программного решения проводилось по схеме, приведённой на рисунках 1–4.")]
        for n in range(1, 5):
            ip, cp = new_picture(doc, DIAG / f"testing-scheme-{n}.png",
                                  f"Схема тестирования часть {n}", 14.5)
            nodes += [ip, cp]
        nodes += [new_para(doc, "3.2. Требования, подлежащие проверке", h3s)]
        for line in [
            "интерфейс: переключение страниц, адаптивность, работа форм;",
            "регистрация и авторизация: вход, выход, блокировка после трёх неудачных попыток, 2FA;",
            "роль «Гость»: поиск и бронирование номера, просмотр счетов, заказ услуг, отзывы;",
            "роль «Менеджер»: бронирования, шахматка, заселение, folio, отчёты, лист ожидания;",
            "роль «Хаускипинг»: задания, расходники, заявки на ремонт;",
            "роль «Управляющий»: справочники, сотрудники, отчёты, аудит;",
            "роль «Администратор БД»: пользователи, роли, бэкапы, мониторинг;",
            "целостность данных: ограничения, триггеры, транзакции, защита от SQL-инъекций.",
        ]:
            nodes.append(new_para(doc, "• " + line))
        p_sred._p.addprevious(nodes[0]._p)
        insert_after(nodes[0], *nodes[1:])
        p_sred._p.addprevious(new_para(doc, "4. СРЕДСТВА И ПОРЯДОК ИСПЫТАНИЙ", h2s)._p)
    if 0 <= i_met < e:
        p_met._p.addprevious(new_para(doc, "5. МЕТОДЫ ИСПЫТАНИЙ", h2s)._p)

    # One combined test table in the exact format of the previous course PZ.
    # Remove the old separate test tables inside this appendix first.
    cur = list(doc.paragraphs)
    v_idx = next((i for i, p in enumerate(cur)
                  if p.alignment == 2 and text_of(p).startswith(PRILOZ + " В")), -1)
    g_idx = next((i for i, p in enumerate(cur)
                  if i > v_idx and p.alignment == 2 and text_of(p).startswith(PRILOZ + " Г")),
                 len(cur))
    if v_idx >= 0:
        v_el, g_el = cur[v_idx]._p, cur[g_idx]._p
        children = list(doc.element.body)
        i0 = children.index(v_el)
        i1 = children.index(g_el) if g_el in children else len(children)
        for t in list(doc.tables):
            el = t._tbl
            if el in children and i0 <= children.index(el) < i1:
                el.getparent().remove(el)

        anchor = next((p for p in doc.paragraphs
                       if text_of(p).startswith("6. Тестовые примеры") and p.style.name == h2s), None)
        if anchor is not None:
            cap = new_para(doc, "Таблица 1. Тестовые сценарии и результаты испытаний", size=12, bold=True)
            tbl = new_table(doc, test_cases.HEADERS, test_cases.rows(),
                            widths=[0.8, 4.8, 4.8, 4.2, 1.6])
            anchor._p.addnext(cap._p)
            cap._p.addnext(tbl._tbl)


# ------------------------------------------------------------------ appendix Г
def enrich_g(doc: Document, s: int, e: int):
    paras = doc.paragraphs
    h2s, h3s = h2_style(doc), h3_style(doc)
    i_usl, p_usl = find(doc, lambda t: t.startswith("1. Условия использования"), s)
    if i_usl < 0 or i_usl > e:
        return
    insert_after(p_usl,
        new_para(doc, "Таблица 1. Минимальные и рекомендованные требования", size=12, bold=True),
        new_table(doc, ["Параметр", "Минимальные", "Рекомендованные"], [
            ["Процессор", "2 ядра", "4 ядра"],
            ["Оперативная память", "4 ГБ", "8 ГБ"],
            ["Место на диске", "10 ГБ", "20 ГБ"],
            ["Браузер", "Chromium / Firefox", "Chromium (последняя версия)"],
            ["С УБД", "PostgreSQL 16", "PostgreSQL 16"],
            ["Сеть", "10 Мбит/с", "100 Мбит/с"],
        ], widths=[4.5, 5.5, 5.5]),
        new_para(doc, "Таблица 2. Программные средства", size=12, bold=True),
        new_table(doc, ["Средство", "Назначение"], [
            ["Python 3.13 + FastAPI", "Серверная логика и REST API"],
            ["React 18 + TypeScript", "Клиентское одностраничное приложение"],
            ["PostgreSQL 16", "Хранение данных гостиницы"],
            ["Nginx", "Статический хостинг и проксирование"],
            ["Docker Compose", "Локальный запуск сервисов"],
            ["pytest / Playwright", "Автоматическое и браузерное тестирование"],
            ["pg_dump / pg_restore", "Резервное копирование и восстановление"],
        ], widths=[6.0, 9.5]))

    # Real screenshots captured from the deployed SunStay site.
    shots = {
        "Гость": [
            ("real-home.jpg", "Главная страница сайта"),
            ("real-search.jpg", "Поиск доступных номеров"),
            ("real-guest-home.jpg", "Личный кабинет гостя"),
            ("real-guest-bookings.jpg", "Мои бронирования"),
            ("real-guest-services.jpg", "Дополнительные услуги"),
            ("real-guest-invoices.jpg", "Счета и платежи"),
            ("real-guest-loyalty.jpg", "Бонусные баллы"),
            ("real-guest-profile.jpg", "Профиль и настройки"),
        ],
        "Менеджер": [
            ("real-manager-dashboard.jpg", "Дашборд менеджера"),
            ("real-manager-bookings.jpg", "Реестр бронирований"),
            ("real-manager-grid.jpg", "Шахматка номеров"),
            ("real-manager-folios.jpg", "Folio и платежи"),
            ("real-manager-waitlist.jpg", "Лист ожидания"),
            ("real-manager-reports.jpg", "Отчёты и аналитика"),
        ],
        "Хаускипинг": [
            ("real-hk-board.jpg", "Доска хаускипинга"),
            ("real-hk-maintenance.jpg", "Заявки на техобслуживание"),
        ],
        "Администратор БД": [
            ("real-admin-dashboard.jpg", "Дашборд администратора"),
            ("real-admin-users.jpg", "Пользователи и роли"),
            ("real-admin-audit.jpg", "Журнал аудита"),
            ("real-admin-backups.jpg", "Резервное копирование"),
            ("real-admin-reviews.jpg", "Модерация отзывов"),
            ("real-admin-floor-plan.jpg", "План этажа"),
            ("real-admin-directories.jpg", "Справочники отеля"),
            ("real-admin-maintenance.jpg", "Заявки на техобслуживание"),
            ("real-admin-settings.jpg", "Настройки"),
        ],
    }
    for role, files in shots.items():
        # always search fresh: previous insertions shift all indices
        cur = list(doc.paragraphs)
        g_idx = next((i for i, p in enumerate(cur)
                      if p.alignment == 2 and text_of(p).startswith(PRILOZ + " Г")), -1)
        d_idx = next((i for i, p in enumerate(cur)
                      if p.alignment == 2 and text_of(p).startswith(PRILOZ + " Д")), len(cur))
        idx = next((i for i, p in enumerate(cur)
                    if g_idx < i < d_idx and text_of(p) == role), -1)
        if idx < 0:
            continue
        q = cur[idx + 1]
        nodes = []
        for n, (fn, caption) in enumerate(files):
            ip, cp = new_picture(doc, SHOTS / fn,
                                  f"Рисунок {n+1}. {role} — {caption}", 14.0)
            nodes += [ip, cp]
        insert_after(q, *nodes)

    # extend appendix TOC with detailed subsections (fresh indices again)
    cur = list(doc.paragraphs)
    g_idx = next((i for i, p in enumerate(cur)
                  if p.alignment == 2 and text_of(p).startswith(PRILOZ + " Г")), -1)
    d_idx = next((i for i, p in enumerate(cur)
                  if p.alignment == 2 and text_of(p).startswith(PRILOZ + " Д")), len(cur))
    toc_idx = next((i for i in range(g_idx, d_idx)
                    if text_of(cur[i]).lower() == SODER.lower()), -1)
    if toc_idx >= 0:
        paras = cur
        last = cur[toc_idx]
        for j in range(toc_idx + 1, min(toc_idx + 20, d_idx)):
            if paras[j].style.name.startswith(SODER):
                last = paras[j]
        extra = ["2.1. Действия для запуска программы", "2.2. Выполнение программы с описанием функций",
                 "2.2.1. Гость", "2.2.2. Менеджер", "2.2.3. Хаускипинг",
                 "2.2.4. Управляющий отелем", "2.2.5. Администратор базы данных"]
        for label in extra:
            np = new_para(doc, label + "\t3", style=SODER + " приложения", size=14)
            insert_after(last, np)
            last = np
        # make numbered role headings match the TOC labels
        renames = {"Гость": "2.2.1. Гость", "Менеджер": "2.2.2. Менеджер",
                   "Хаускипинг": "2.2.3. Хаускипинг", "Администратор БД": "2.2.5. Администратор базы данных"}
        for pp in doc.paragraphs:
            label = text_of(pp)
            if pp.style.name == h3s and label in renames:
                for r in list(pp.runs):
                    r._r.getparent().remove(r._r)
                set_font(pp.add_run(renames[label]), 14, True)


# ------------------------------------------------------------------ appendix Д
def enrich_d(doc: Document, s: int, e: int):
    paras = doc.paragraphs
    h2s, h3s = h2_style(doc), h3_style(doc)
    i_nom, p_nom = find(doc, lambda t: t.startswith("Наименование скрипта"), s)
    i_obl, p_obl = find(doc, lambda t: t.startswith("Область применения"), s)
    i4, p4 = -1, None
    for j, pp in enumerate(doc.paragraphs):
        if j > s and text_of(pp).startswith("1.4. Скрипт") and not pp.style.name.startswith(SODER):
            i4, p4 = j, pp
            break
    if i_nom < 0 or i_nom > e:
        return
    head = new_para(doc, "1. СКРИПТ БАЗЫ ДАННЫХ", h2s)
    sub = new_para(doc, "1.1. Наименование скрипта", h3s)
    p_nom._p.addprevious(head._p)
    head._p.addnext(sub._p)
    if 0 <= i_obl < e:
        p_obl._p.addprevious(new_para(doc, "1.2. Область применения скрипта", h3s)._p)
    if 0 <= i4 < e:
        cap = new_para(doc, "Таблица 1. Словарь данных базы данных", size=12, bold=True)
        tbl = new_table(doc, ["Таблица", "Поле", "Тип", "Описание"], [
            ["users", "user_id", "SERIAL", "Идентификатор пользователя"],
            ["users", "email", "VARCHAR", "Электронная почта"],
            ["users", "role_id", "INTEGER", "Роль пользователя"],
            ["hotels", "hotel_id", "SERIAL", "Идентификатор отеля"],
            ["rooms", "room_id", "SERIAL", "Идентификатор номера"],
            ["room_types", "type_id", "SERIAL", "Тип номера"],
            ["rates", "rate_id", "SERIAL", "Тариф"],
            ["bookings", "booking_id", "SERIAL", "Идентификатор брони"],
            ["bookings", "check_in", "DATE", "Дата заезда"],
            ["bookings", "check_out", "DATE", "Дата выезда"],
            ["bookings", "status", "VARCHAR", "Статус брони"],
            ["guests", "guest_id", "SERIAL", "Идентификатор гостя"],
            ["folio", "folio_id", "SERIAL", "Счёт гостя"],
            ["payments", "payment_id", "SERIAL", "Платёж"],
            ["services", "service_id", "SERIAL", "Дополнительная услуга"],
            ["reviews", "review_id", "SERIAL", "Отзыв гостя"],
            ["housekeeping_tasks", "task_id", "SERIAL", "Задание хаускипинга"],
            ["audit_log", "log_id", "BIGSERIAL", "Запись журнала аудита"],
            ["backups", "backup_id", "SERIAL", "Резервная копия"],
        ], widths=[3.5, 3.5, 3.0, 6.5])
        head_d = new_para(doc, "1.3. Словарь данных базы данных", h3s)
        p4._p.addprevious(head_d._p)
        head_d._p.addnext(cap._p)
        cap._p.addnext(tbl._tbl)


def process(path: Path):
    doc = Document(str(path))
    # 1) all tables plain, no coloured fill
    for t in doc.tables:
        strip_shading(t)
    for el in doc.element.body.iter(W + "shd"):
        el.getparent().remove(el)

    # 2) enrich each appendix when this is the full PZ
    prefixes = [PRILOZ + " Б", PRILOZ + " В", PRILOZ + " Г", PRILOZ + " Д"]
    fns = [enrich_b, enrich_v, enrich_g, enrich_d]
    def title_of(prefix):
        for p in doc.paragraphs:
            if text_of(p).startswith(prefix) and p.alignment == 2:
                return text_of(p)
        return prefix
    for prefix, fn in zip(prefixes, fns):
        bounds = region_bounds(doc, title_of(prefix))
        if bounds:
            fn(doc, *bounds)

    # 3) link every appendix TOC entry (after enrichment, so new headings exist)
    total = 0
    for prefix in prefixes:
        bounds = region_bounds(doc, title_of(prefix))
        if bounds:
            total += link_appendix_toc(doc, *bounds)

    doc.save(str(path))
    print("ENRICHED", path.name, "links", total,
          "tables", len(doc.tables), "imgs", len(doc.inline_shapes))


if __name__ == "__main__":
    for name in ["Пояснительная_записка_SunStay.docx", "Пояснительная_записка_без_титульника.docx"]:
        p = DOCS / name
        if p.exists():
            process(p)
