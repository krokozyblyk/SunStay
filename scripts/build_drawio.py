"""Generate draw.io sources for SunStay diagrams in the style of the previous course project."""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parents[1] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#1a237e"
LIGHT = "#90caf9"
LINE = "#1976d2"


def cell(i, value, x, y, w, h, fill=LIGHT, font="#000000", style="rounded=1"):
    return (f'        <mxCell id="n{i}" value="{escape(value)}" '
            f'style="{style};whiteSpace=wrap;html=1;fillColor={fill};strokeColor={LINE};fontColor={font};fontStyle=1;fontSize=11;" '
            f'parent="1" vertex="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" /></mxCell>')


def edge(i, s, t):
    return (f'        <mxCell id="e{i}" style="endArrow=classic;html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;" '
            f'parent="1" source="n{s}" target="n{t}" edge="1"><mxGeometry relative="1" as="geometry" /></mxCell>')


def wrap(title, cells):
    return ('<mxfile host="Electron" version="24.7.17">\n'
            '  <diagram name="' + escape(title) + '">\n'
            '    <mxGraphModel dx="1600" dy="1000" grid="1" page="1" pageWidth="1600" pageHeight="1100">\n'
            '      <root><mxCell id="0" /><mxCell id="1" parent="0" />\n'
            + "\n".join(cells) + '\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n')


def use_case():
    c = [cell(1, 'Схема прецедентов СИ «SunStay»', 350, 20, 800, 40, BLUE, "#ffffff", "rounded=0")]
    roles = ["Гость", "Менеджер", "Хаускипинг", "Управляющий", "Админ БД"]
    for i, r in enumerate(roles, 2):
        c.append(cell(i, r, 60 + (i - 2) * 290, 100, 220, 45))
    cases = ["Поиск и бронирование", "Оплата и услуги", "Заселение и выселение", "Folio и платежи",
             "Задания уборки", "Отчёты", "Пользователи и роли", "Бэкапы и аудит"]
    for j, name in enumerate(cases):
        c.append(cell(10 + j, name, 60 + (j % 4) * 290, 220 + (j // 4) * 200, 220, 60, "#e3f2fd"))
    for i in range(2, 7):
        c.append(edge(100 + i, i, 10 + (i - 2)))
    c.append(edge(200, 1, 3))
    return wrap("Диаграмма прецедентов", c)


def erd():
    c = [cell(1, 'Логическая и физическая модель данных «SunStay»', 300, 20, 900, 40, BLUE, "#ffffff", "rounded=0")]
    tables = [("users", "user_id, role_id, email, password_hash"),
              ("guests", "guest_id, user_id, full_name, document_number_hash"),
              ("rooms", "room_id, room_type_id, status_id, room_number"),
              ("room_types", "room_type_id, name, capacity"),
              ("bookings", "booking_id, guest_id, room_id, rate_id, dates"),
              ("folios", "folio_id, booking_id, status, balance"),
              ("payments", "payment_id, folio_id, amount, method"),
              ("housekeeping_tasks", "task_id, room_id, staff_id, status")]
    for i, (name, fields) in enumerate(tables, 2):
        c.append(cell(i, f"{name}\n{fields}", 50 + ((i - 2) % 4) * 370, 110 + ((i - 2) // 4) * 230, 320, 100, "#e3f2fd"))
    for i, t in enumerate([3, 5, 5, 6, 6, 7, 9], 2):
        c.append(edge(100 + i, i, t))
    return wrap("ERD", c)


def functional():
    c = [cell(1, 'Функциональная схема информационной системы «SunStay»', 250, 20, 1000, 40, BLUE, "#ffffff", "rounded=0")]
    roles = ["Гость", "Менеджер", "Хаускипинг", "Администратор БД"]
    for i, r in enumerate(roles, 2):
        c.append(cell(i, r, 60 + (i - 2) * 370, 110, 250, 45))
    groups = ["Публичный сайт: поиск, бронь, отзывы", "Операции: брони, заезд, folio, отчёты",
              "Обслуживание: задания, расходники, ремонт", "Администрирование: users, роли, бэкапы"]
    for j, g in enumerate(groups):
        c.append(cell(10 + j, g, 60 + j * 370, 240, 250, 70, "#e3f2fd"))
    for i in range(2, 6):
        c.append(edge(100 + i, i, 8 + i))
    c.append(cell(20, 'Общая БД PostgreSQL', 350, 400, 800, 50, BLUE, "#ffffff"))
    for j in range(10, 14):
        c.append(edge(200 + j, j, 20))
    return wrap("Функциональная схема", c)


def interface():
    c = [cell(1, 'Схема пользовательского интерфейса «SunStay»', 300, 20, 900, 40, BLUE, "#ffffff", "rounded=0")]
    items = ["Главная и поиск", "Каталог номеров", "Страница номера", "Оформление брони",
             "Личный кабинет гостя", "Дашборд менеджера", "Шахматка", "Folio и платежи",
             "Доска хаускипинга", "Отчёты", "Админ-панель", "Настройки"]
    for i, name in enumerate(items, 2):
        c.append(cell(i, name, 50 + ((i - 2) % 4) * 370, 100 + ((i - 2) // 4) * 190, 250, 70, "#e3f2fd"))
    for i in range(2, 5):
        c.append(edge(100 + i, 1, i))
    for i in range(5, 14):
        c.append(edge(100 + i, 2, i))
    return wrap("Схема интерфейса", c)


def main():
    for name, data in [("Диаграмма_прецедентов_SunStay.drawio", use_case()),
                       ("ERD_SunStay.drawio", erd()),
                       ("Функциональная_схема_SunStay.drawio", functional()),
                       ("Схема_интерфейса_SunStay.drawio", interface())]:
        (OUT / name).write_text(data, encoding="utf-8")
        print("Saved:", name)


if __name__ == "__main__":
    main()
