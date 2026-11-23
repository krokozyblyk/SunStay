"""Redraw all SunStay diagrams as clean black-and-white figures."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram_lib import Canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def entity(c, box, name, fields, tsize=30, fsize=22):
    x1, y1, x2, y2 = box
    c.d.rectangle([x1, y1, x2, y2], outline="black", width=4, fill="white")
    c.d.line([(x1, y1 + 56), (x2, y1 + 56)], fill="black", width=3)
    c.text((x1 + x2) / 2, y1 + 28, name, tsize, True)
    y = y1 + 84
    for fld in fields:
        c.text(x1 + 16, y, fld, fsize, False, anchor="lm")
        y += fsize + 14


def table(c, box, name, fields, tsize=28, fsize=21):
    x1, y1, x2, y2 = box
    c.d.rectangle([x1, y1, x2, y2], outline="black", width=4, fill="white")
    c.d.rectangle([x1, y1, x2, y1 + 54], fill="black")
    c.text((x1 + x2) / 2, y1 + 27, name, tsize, True)
    # white text on the black header
    c.d.text(((x1 + x2) / 2, y1 + 27), name, font=__import__("diagram_lib").font(tsize, True),
             fill="white", anchor="mm")
    y = y1 + 80
    for fld in fields:
        c.text(x1 + 14, y, fld, fsize, False, anchor="lm")
        y += fsize + 12


# ------------------------------------------------------------------ 1. architecture
def architecture():
    c = Canvas(2400, 840)
    c.box(70, 280, 470, 560, "Клиент", "Браузер · React SPA", 34, 25)
    c.box(600, 280, 1000, 560, "Nginx", "статика и прокси", 34, 25)
    c.box(1140, 110, 1620, 380, "Core API", "FastAPI · бизнес-логика, RBAC", 34, 25)
    c.box(1140, 480, 1620, 750, "Analytics API", "FastAPI · отчётность (read-only)", 34, 24)
    c.box(1800, 260, 2320, 600, "PostgreSQL 16", "37 таблиц · 14 представлений", 34, 25)
    c.box(1800, 660, 2320, 810, "Планировщик", "pg_dump · резервные копии", 30, 22)
    c.arrow([(470, 420), (600, 420)])
    c.text(535, 395, "HTTPS", 22)
    c.arrow([(1000, 350), (1070, 350), (1070, 245), (1140, 245)])
    c.text(1050, 225, "REST/JSON", 20, anchor="rm")
    c.arrow([(1000, 480), (1070, 480), (1070, 615), (1140, 615)])
    c.text(1050, 645, "REST/JSON", 20, anchor="rm")
    c.arrow([(1620, 245), (1700, 245), (1700, 360), (1800, 360)])
    c.text(1712, 300, "SQL", 20, anchor="lm")
    c.arrow([(1620, 615), (1700, 615), (1700, 500), (1800, 500)])
    c.text(1720, 650, "SQL (read)", 20, anchor="lm")
    c.arrow([(2060, 600), (2060, 660)])
    c.text(2075, 630, "pg_dump", 20, anchor="lm")
    c.save(OUT / "architecture.png")


# ------------------------------------------------------------------ 2. components
def components():
    c = Canvas(2400, 1193)
    c.frame(50, 50, 730, 660, "Клиент · React SPA")
    for i, t in enumerate(["App.tsx — маршрутизация", "lib/api.ts — REST-клиент",
                           "components/ui.tsx — UI", "pages — экраны и формы"]):
        c.box(80, 130 + i * 125, 700, 235 + i * 125, t, None, 27)
    c.frame(840, 50, 1600, 660, "Core API · FastAPI")
    core = ["auth.py — вход и 2FA", "public.py — каталог", "manager.py — операции",
            "admin.py — администрирование", "services/ — бэкапы", "notifications.py — письма"]
    for i, t in enumerate(core):
        col, row = divmod(i, 3)
        c.box(870 + col * 350, 130 + row * 165, 1205 + col * 350, 270 + row * 165, t, None, 24)
    c.frame(1700, 50, 2350, 420, "Analytics API")
    c.box(1730, 140, 2320, 260, "reports.py — отчёты", None, 26)
    c.box(1730, 290, 2320, 400, "export.py — CSV и PNG", None, 26)
    c.frame(1700, 460, 2350, 930, "PostgreSQL 16")
    for i, t in enumerate(["users · roles", "bookings · rooms",
                           "folios · payments", "audit · housekeeping"]):
        c.box(1730, 540 + i * 90, 2320, 615 + i * 90, t, None, 24)
    c.frame(50, 710, 1600, 1120, "Инфраструктура")
    for i, t in enumerate(["Nginx", "Docker Compose", "GitHub Actions", "pg_dump / pg_restore"]):
        c.box(80 + i * 375, 800, 420 + i * 375, 1040, t, None, 25)
    c.arrow([(730, 355), (840, 355)])
    c.text(785, 330, "REST", 22)
    c.arrow([(1600, 250), (1700, 250)])
    c.text(1650, 290, "чтение", 20)
    c.arrow([(2025, 420), (2025, 460)])
    c.text(2065, 440, "SQL", 20, anchor="lm")
    c.arrow([(1000, 710), (1000, 660)], dashed=True)
    c.text(1030, 690, "развёртывание", 20, anchor="lm")
    c.save(OUT / "components.png")


# ------------------------------------------------------------------ 3. dataflow
def dataflow():
    c = Canvas(2400, 1193)
    actors = [(260, "Гость"), (700, "React SPA"), (1150, "Nginx"),
              (1600, "Core API"), (2050, "PostgreSQL")]
    for x, name in actors:
        c.box(x - 150, 70, x + 150, 190, name, None, 28)
        c.line([(x, 190), (x, 1140)], lw=3, dashed=True)
    msgs = [
        (260, 700, 320, "ввод данных и поиск"),
        (700, 1150, 440, "HTTPS-запрос"),
        (1150, 1600, 560, "проксирование"),
        (1600, 2050, 680, "SQL-запрос"),
        (2050, 1600, 790, "результат", True),
        (1600, 1150, 900, "JSON-ответ", True),
        (1150, 700, 1010, "HTTP-ответ", True),
        (700, 260, 1120, "отображение", True),
    ]
    for x1, x2, y, label, *rest in msgs:
        dashed = rest[0] if rest else False
        c.arrow([(x1, y), (x2, y)], dashed=dashed, label=label, label_off=(0, -22))
    c.save(OUT / "dataflow.png")


# ------------------------------------------------------------------ 4. logical ERD
def erd():
    c = Canvas(2400, 1531)
    B = {
        "users": (80, 120, 560, 400, ["user_id PK", "role_id FK", "email", "password_hash"]),
        "tasks": (640, 120, 1120, 400, ["task_id PK", "room_id FK", "status", "assignee_id"]),
        "rooms": (1200, 120, 1680, 400, ["room_id PK", "type_id FK", "number", "floor", "status"]),
        "types": (1760, 120, 2240, 400, ["type_id PK", "name", "capacity", "base_price"]),
        "guests": (80, 560, 560, 840, ["guest_id PK", "last_name", "first_name", "phone"]),
        "bookings": (640, 470, 1120, 930, ["booking_id PK", "guest_id FK", "room_id FK",
                                            "rate_id FK", "check_in / check_out", "status"]),
        "rates": (1200, 560, 1680, 840, ["rate_id PK", "type_id FK", "name", "price"]),
        "services": (80, 1000, 560, 1280, ["service_id PK", "name", "price"]),
        "folios": (1200, 1000, 1680, 1280, ["folio_id PK", "booking_id FK", "balance", "status"]),
        "payments": (1760, 1000, 2240, 1280, ["payment_id PK", "folio_id FK", "amount", "method"]),
    }
    for name, (x1, y1, x2, y2, flds) in B.items():
        entity(c, (x1, y1, x2, y2), name, flds)
    c.connect(B["users"], B["bookings"], "r", "l", "1", "M")
    c.connect(B["guests"], B["bookings"], "r", "l", "1", "M")
    c.connect(B["services"], B["bookings"], "r", "l", "M", "M")
    c.connect(B["tasks"], B["rooms"], "r", "l", "M", "1")
    c.connect(B["rooms"], B["bookings"], "l", "r", "1", "M")
    c.connect(B["rates"], B["bookings"], "l", "r", "1", "M")
    c.connect(B["folios"], B["bookings"], "l", "r", "1", "1")
    c.connect(B["types"], B["rooms"], "l", "r", "1", "M")
    c.connect(B["payments"], B["folios"], "l", "r", "M", "1")
    c.save(OUT / "erd.png")


# ------------------------------------------------------------------ 5. functional
def functional():
    c = Canvas(1400, 2001)
    c.box(420, 40, 980, 150, "SunStay — управление гостиницей", None, 30)
    modules = [
        ("Бронирование", ["поиск доступности", "создание и отмена брони", "подтверждение и оплата"]),
        ("Заселение и выезд", ["заселение гостя", "холд и документы", "выселение и закрытие счёта"]),
        ("Биллинг и услуги", ["folio и начисления", "платежи и возвраты", "дополнительные услуги"]),
        ("Хаускипинг", ["задания на уборку", "статусы номеров", "расходники и заявки"]),
        ("Отчётность", ["загрузка и ADR", "RevPAR и отмены", "экспорт CSV / PNG"]),
        ("Администрирование", ["пользователи и роли", "аудит и бэкапы", "справочники и настройки"]),
    ]
    top, h, gap = 200, 270, 28
    last_cy = top + 5 * (h + gap) + h / 2
    c.line([(700, 150), (700, 175), (80, 175), (80, last_cy)])
    for i, (title, subs) in enumerate(modules):
        y = top + i * (h + gap)
        c.plain(120, y, 1360, y + h, lw=4, radius=14)
        c.text(150, y + 45, title, 32, True, anchor="lm")
        for j, s in enumerate(subs):
            c.text(175, y + 100 + j * 52, "• " + s, 26, False, anchor="lm")
        cy = y + h / 2
        c.line([(80, cy), (120, cy)], lw=4)
    c.save(OUT / "functional.png")


# ------------------------------------------------------------------ 6. test pyramid
def testpyramid():
    c = Canvas(2400, 928)
    cx = 1200
    levels = [(120, 40, "E2E"), (300, 420, "Интеграционные тесты"),
              (500, 900, "API-тесты · pytest"), (700, 1600, "SQL-тесты · база данных")]
    ys = [120, 300, 500, 700, 840]
    widths = [40, 420, 900, 1600, 2000]
    for i in range(4):
        y1, y2 = ys[i], ys[i + 1]
        w1, w2 = widths[i] / 2, widths[i + 1] / 2
        pts = [(cx - w1, y1), (cx + w1, y1), (cx + w2, y2), (cx - w2, y2)]
        c.d.polygon(pts, outline="black", fill="white")
        c.d.line(pts + [pts[0]], fill="black", width=4)
        label = levels[i][2]
        c.block(cx, (y1 + y2) / 2 + (10 if i == 0 else 0), label, 28, True, (w1 + w2) - 60)
    c.save(OUT / "testpyramid.png")


# ------------------------------------------------------------------ 7. testing flow
def testing_flow():
    c = Canvas(2400, 1193)
    row1 = [(120, "Планирование тестов"), (880, "Подготовка данных"), (1640, "Выполнение тестов")]
    row2 = [(1640, "Фиксация результатов"), (880, "Анализ дефектов"), (120, "Итоговый отчёт")]
    for x, t in row1:
        c.box(x, 150, x + 640, 450, t, None, 31)
    for x, t in row2:
        c.box(x, 720, x + 640, 1020, t, None, 31)
    c.arrow([(760, 300), (880, 300)])
    c.arrow([(1520, 300), (1640, 300)])
    c.arrow([(1960, 450), (1960, 720)])
    c.arrow([(1640, 870), (1520, 870)])
    c.arrow([(880, 870), (760, 870)])
    c.arrow([(1200, 720), (1200, 620), (2140, 620), (2140, 450)], dashed=True)
    c.text(1640, 590, "повторный прогон", 22)
    c.save(OUT / "testing-flow.png")


# ------------------------------------------------------------------ 8. booking flow
def booking_flow():
    c = Canvas(2400, 1192)
    c.box(120, 120, 700, 280, "Поиск доступности", None, 28)
    c.box(820, 120, 1400, 280, "Выбор номера", None, 28)
    c.box(1520, 120, 2100, 280, "Создание брони", None, 28)
    c.diamond(1910, 470, 560, 200, "Даты свободны?")
    c.box(1520, 640, 2100, 800, "Подтверждение", None, 28)
    c.box(1520, 900, 2100, 1040, "Отказ: даты заняты", None, 26)
    c.box(820, 640, 1400, 800, "Заселение", None, 28)
    c.box(120, 640, 700, 800, "Folio и услуги", None, 28)
    c.box(120, 900, 700, 1040, "Выселение", None, 28)
    c.box(820, 900, 1400, 1040, "Начисление бонусов", None, 27)
    c.arrow([(700, 200), (820, 200)])
    c.arrow([(1400, 200), (1520, 200)])
    c.arrow([(1910, 280), (1910, 370)])
    c.arrow([(1910, 570), (1850, 570), (1850, 640)], label="да", label_off=(60, -10))
    c.arrow([(2190, 470), (2280, 470), (2280, 970), (2100, 970)])
    c.text(2250, 930, "нет", 22)
    c.arrow([(1520, 720), (1400, 720)])
    c.arrow([(820, 720), (700, 720)])
    c.arrow([(410, 800), (410, 900)])
    c.arrow([(700, 970), (820, 970)])
    c.save(OUT / "booking-flow.png")


# ------------------------------------------------------------------ 9. room states
def room_states():
    c = Canvas(2400, 1192)
    st = {
        "free": (120, 140, 520, 300, "Свободен"),
        "ready": (900, 120, 1400, 280, "Готов"),
        "booked": (1720, 140, 2160, 300, "Забронирован"),
        "in": (1720, 500, 2160, 660, "Заселён"),
        "dirty": (1720, 880, 2160, 1040, "Грязный"),
        "clean": (900, 880, 1400, 1040, "Уборка"),
        "blocked": (120, 500, 520, 660, "Заблокирован"),
    }
    for x1, y1, x2, y2, t in st.values():
        c.box(x1, y1, x2, y2, t, None, 30, radius=28)
    c.arrow([(520, 220), (900, 220)], label="готов к продаже", label_off=(0, -20))
    c.arrow([(1400, 200), (1720, 200)], label="создана бронь", label_off=(0, -20))
    c.arrow([(1940, 300), (1940, 500)], label="заселение", label_off=(90, 0))
    c.arrow([(1940, 660), (1940, 880)], label="выезд", label_off=(60, 0))
    c.arrow([(1720, 960), (1400, 960)], label="начата уборка", label_off=(0, -20))
    c.arrow([(1150, 880), (1150, 280)], label="уборка завершена", label_off=(95, 0))
    c.biarrow([(900, 240), (820, 240), (820, 600), (520, 600)])
    c.text(670, 575, "блокировка ↔ разблокировка", 20)
    c.save(OUT / "room-states.png")


# ------------------------------------------------------------------ 10. UI map
def uimap():
    c = Canvas(2400, 858)
    c.box(1020, 40, 1380, 150, "SunStay Web", None, 32)
    cols = [
        ("Публичная часть", ["Главная", "Поиск номеров", "Оформление брони", "Вход"]),
        ("Гость", ["Кабинет", "Мои брони", "Услуги и счета", "Профиль"]),
        ("Менеджер", ["Дашборд", "Шахматка", "Бронирования", "Folio"]),
        ("Хаускипинг", ["Задания", "Статусы", "Расходники", "Заявки"]),
        ("Управляющий", ["Отчёты", "Справочники", "Сотрудники", "Аудит"]),
        ("Админ БД", ["Пользователи", "Бэкапы", "Мониторинг", "Настройки"]),
    ]
    xs = [50, 440, 830, 1220, 1610, 2000]
    trunk_y = 190
    c.line([(1200, 150), (1200, trunk_y)], lw=4)
    c.line([(xs[0] + 175, trunk_y), (xs[-1] + 175, trunk_y)], lw=4)
    for (title, items), x in zip(cols, xs):
        cx = x + 175
        c.line([(cx, trunk_y), (cx, 240)], lw=4)
        c.box(x, 240, x + 350, 330, title, None, 27)
        for j, it in enumerate(items):
            c.box(x + 20, 370 + j * 110, x + 330, 460 + j * 110, it, None, 22)
    c.save(OUT / "uimap.png")


# ------------------------------------------------------------------ testing schemes 1-4
def scheme(name, items):
    c = Canvas(2400, 1012)
    xs = [120, 850, 1580]
    for row in range(2):
        for col in range(3):
            i = row * 3 + col
            x = xs[col]
            y = 120 + row * 460
            c.box(x, y, x + 640, y + 300, items[i], None, 30)
    c.arrow([(760, 270), (850, 270)])
    c.arrow([(1490, 270), (1580, 270)])
    c.arrow([(1900, 420), (1900, 580)])
    c.arrow([(1580, 730), (1490, 730)])
    c.arrow([(850, 730), (760, 730)])
    c.save(OUT / name)


def scheme_roles():
    c = Canvas(2400, 1012)
    roles = ["Гость", "Менеджер", "Хаускипинг", "Управляющий отелем", "Администратор БД"]
    xs = [50, 520, 990, 1460, 1930]
    centers = []
    for x, t in zip(xs, roles):
        c.box(x, 140, x + 420, 380, t, None, 27)
        centers.append(x + 210)
    bus_y = 600
    for cx in centers:
        c.line([(cx, 380), (cx, bus_y)], lw=4)
    c.line([(centers[0], bus_y), (centers[-1], bus_y)], lw=4)
    c.box(800, 720, 1600, 950, "Итоговая оценка", None, 31)
    c.arrow([(1200, bus_y), (1200, 720)])
    c.save(OUT / "testing-scheme-2.png")


# ------------------------------------------------------------------ conceptual ERD
def conceptual_erd():
    c = Canvas(2400, 1500)
    boxes = {
        "guest": (100, 140, 600, 380, "Гость"),
        "task": (950, 100, 1450, 340, "Задание хаускипинга"),
        "room": (1800, 140, 2300, 380, "Номер"),
        "type": (1850, 620, 2350, 860, "Тип номера"),
        "rate": (1800, 1080, 2300, 1320, "Тариф"),
        "serv": (950, 1120, 1450, 1360, "Услуга"),
        "folio": (100, 1080, 600, 1320, "Счёт (folio)"),
        "pay": (100, 620, 600, 860, "Платёж"),
    }
    for x1, y1, x2, y2, t in boxes.values():
        c.box(x1, y1, x2, y2, t, None, 32, radius=22)
    c.box(850, 560, 1550, 880, "Бронирование", None, 34, radius=24)

    def rel(p1, p2, la="1", lb="M"):
        c.arrow([p1, p2])
        c.text(p1[0] + (36 if p2[0] >= p1[0] else -36),
               p1[1] + (-36 if p2[1] <= p1[1] else 36), la, 24, True)
        c.text(p2[0] + (-36 if p2[0] >= p1[0] else 36),
               p2[1] + (36 if p2[1] <= p1[1] else -36), lb, 24, True)

    rel((600, 300), (850, 580))                     # гость -> бронь
    rel((600, 1170), (850, 860))                    # счёт -> бронь
    c.arrow([(350, 860), (350, 1080)])              # платёж -> счёт
    c.text(370, 940, "M", 24, True); c.text(370, 1050, "1", 24, True)
    rel((1200, 1120), (1200, 880))                  # услуга -> бронь
    c.arrow([(2100, 620), (2100, 380)])             # тип -> номер
    c.text(2120, 480, "M", 24, True); c.text(2120, 400, "1", 24, True)
    c.arrow([(2100, 860), (2100, 1080)])            # тип -> тариф
    c.text(2120, 950, "1", 24, True); c.text(2120, 1050, "M", 24, True)
    rel((1900, 380), (1540, 580))                   # номер -> бронь
    rel((1800, 1160), (1540, 860))                  # тариф -> бронь
    c.arrow([(1450, 220), (1800, 220)])             # задание -> номер
    c.text(1500, 195, "M", 24, True); c.text(1760, 195, "1", 24, True)
    c.save(OUT / "conceptual-erd.png")


# ------------------------------------------------------------------ physical ERD
def physical_erd():
    c = Canvas(2400, 1600)
    c1, c2, c3, c4 = (80, 560), (620, 1100), (1160, 1640), (1700, 2240)
    r1, r2, r3 = (100, 500), (620, 1020), (1140, 1500)
    T = {
        "roles": (c1[0], r1[0], c1[1], r1[1],
                  ["role_id PK", "code", "name", "description"]),
        "users": (c2[0], r1[0], c2[1], r1[1],
                  ["user_id PK", "role_id FK", "email", "password_hash",
                   "is_active", "last_login"]),
        "guests": (c3[0], r1[0], c3[1], r1[1],
                   ["guest_id PK", "last_name", "first_name", "phone",
                    "email", "passport_hash"]),
        "rooms": (c4[0], r1[0], c4[1], r1[1],
                  ["room_id PK", "type_id FK", "number", "floor",
                   "status", "notes"]),
        "payments": (c1[0], r2[0], c1[1], r2[1],
                     ["payment_id PK", "folio_id FK", "amount", "method",
                      "paid_at"]),
        "folios": (c2[0], r2[0], c2[1], r2[1],
                   ["folio_id PK", "booking_id FK", "balance", "status",
                    "created_at"]),
        "bookings": (c3[0], r2[0], c3[1], r2[1],
                     ["booking_id PK", "guest_id FK", "room_id FK",
                      "rate_id FK", "check_in", "check_out", "status"]),
        "rates": (c4[0], r2[0], c4[1], r2[1],
                  ["rate_id PK", "type_id FK", "name", "price",
                   "valid_from", "valid_to"]),
        "services": (c3[0], r3[0], c3[1], r3[1],
                     ["service_id PK", "name", "price", "unit", "is_active"]),
    }
    for name, (x1, y1, x2, y2, flds) in T.items():
        table(c, (x1, y1, x2, y2), name, flds)

    def lab(x, y, s):
        c.text(x, y, s, 24, True)

    c.arrow([(560, 300), (620, 300)])            # roles -> users
    lab(575, 275, "1"); lab(610, 325, "M")
    # users -> bookings through the gap between rows
    c.arrow([(800, 500), (800, 560), (1350, 560), (1350, 620)])
    lab(780, 480, "1"); lab(1310, 600, "M")
    c.arrow([(1440, 500), (1440, 620)])          # guests -> bookings
    lab(1460, 520, "1"); lab(1450, 590, "M")
    c.arrow([(2000, 500), (2000, 560), (1530, 560), (1530, 620)])  # rooms -> bookings
    lab(2020, 520, "1"); lab(1560, 600, "M")
    c.arrow([(1700, 820), (1640, 820)])          # rates -> bookings
    lab(1680, 795, "1"); lab(1650, 845, "M")
    c.arrow([(1160, 820), (1100, 820)])          # bookings -> folios
    lab(1140, 795, "1"); lab(1110, 845, "1")
    c.arrow([(620, 820), (560, 820)])            # folios -> payments
    lab(600, 795, "1"); lab(570, 845, "M")
    c.arrow([(1440, 1020), (1440, 1140)])        # bookings -> services
    lab(1460, 1040, "M"); lab(1460, 1120, "M")
    c.save(OUT / "physical-erd.png")


# ------------------------------------------------------------------ structural
def structural():
    c = Canvas(2400, 1300)
    c.box(1000, 40, 1400, 160, "Веб-сервис SunStay", None, 30)
    groups = [
        ("Клиентская часть", ["React SPA", "маршрутизация", "UI-компоненты", "REST-клиент"]),
        ("Серверная часть", ["Core API", "Analytics API", "бизнес-логика", "RBAC и аудит"]),
        ("Хранилище", ["PostgreSQL 16", "таблицы и индексы", "представления", "резервные копии"]),
        ("Инфраструктура", ["Nginx", "Docker Compose", "GitHub Actions", "мониторинг"]),
    ]
    xs = [(60, 600), (660, 1200), (1260, 1800), (1860, 2340)]
    c.line([(1200, 160), (1200, 210)])
    c.line([(xs[0][0] + 270, 210), (xs[-1][0] + 240, 210)])
    for (title, items), (x1, x2) in zip(groups, xs):
        cx = (x1 + x2) / 2
        c.line([(cx, 210), (cx, 270)])
        c.plain(x1, 270, x2, 1200, lw=3)
        c.text(cx, 320, title, 28, True)
        for j, it in enumerate(items):
            c.box(x1 + 40, 380 + j * 190, x2 - 40, 520 + j * 190, it, None, 24)
    c.save(OUT / "structural.png")


# ------------------------------------------------------------------ MVC
def mvc():
    c = Canvas(2400, 1200)
    c.box(120, 500, 520, 720, "Пользователь", None, 30)
    c.box(900, 120, 1500, 320, "Контроллер", "FastAPI-роутеры", 32, 24)
    c.box(900, 500, 1500, 720, "Модель", "PostgreSQL · psycopg", 32, 24)
    c.box(900, 900, 1500, 1100, "Представление", "React-компоненты", 32, 24)
    c.arrow([(520, 610), (700, 610), (700, 220), (900, 220)],
            label="запрос", label_off=(-40, -18))
    c.arrow([(1200, 320), (1200, 500)], label="SQL", label_off=(50, 0))
    c.arrow([(1200, 720), (1200, 900)], label="данные", label_off=(60, 0))
    c.arrow([(900, 1000), (320, 1000), (320, 720)],
            label="интерфейс", label_off=(-40, -18))
    c.arrow([(1500, 220), (1700, 220), (1700, 1000), (1500, 1000)], dashed=True)
    c.text(1720, 600, "выбор представления", 20, anchor="lm")
    c.save(OUT / "mvc.png")


def main():
    architecture()
    components()
    dataflow()
    erd()
    functional()
    testpyramid()
    testing_flow()
    booking_flow()
    room_states()
    uimap()
    scheme("testing-scheme-1.png", ["Требования к системе", "SQL-тесты базы данных",
                                     "API-тесты FastAPI", "UI-тесты React",
                                     "Интеграционные тесты", "Приёмочные тесты"])
    scheme_roles()
    scheme("testing-scheme-3.png", ["Нагрузочные тесты", "Security-тесты", "Проверка RBAC",
                                     "Замеры p95 и RPS", "Блокировка входа",
                                     "Маскирование данных"])
    scheme("testing-scheme-4.png", ["Создание pg_dump", "Восстановление БД", "Сверка таблиц",
                                     "Сверка бронирований", "Ночной аудит", "Итоговый отчёт"])
    conceptual_erd()
    physical_erd()
    structural()
    mvc()


if __name__ == "__main__":
    main()
