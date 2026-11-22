"""Generate additional SunStay diagrams and UI screenshots for the appendices."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "docs" / "diagrams"
SHOTS = ROOT / "docs" / "screenshots"
DIAG.mkdir(parents=True, exist_ok=True)
SHOTS.mkdir(parents=True, exist_ok=True)

FONT = "C:/Windows/Fonts/arial.ttf"
FONT_B = "C:/Windows/Fonts/arialbd.ttf"


def font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT, size)
    except Exception:
        return ImageFont.load_default()


# ---------------------------------------------------------------- testing schemes
def scheme(name, title, items, arrows):
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis("off")
    ax.set_title(title, fontsize=15, fontweight="bold", pad=10)
    pos = {}
    n = len(items)
    for i, text in enumerate(items):
        r, c = divmod(i, 3)
        x = 2 + c * 4
        y = 6.2 - r * 2.0
        pos[i] = (x, y)
        fc = "#e8f4fd" if i % 2 == 0 else "#eaf7ee"
        ec = "#145da0" if i % 2 == 0 else "#1b7a3d"
        box = FancyBboxPatch((x - 1.7, y - 0.6), 3.4, 1.2,
                             boxstyle="round,pad=0.12", facecolor=fc,
                             edgecolor=ec, linewidth=1.6)
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", fontsize=9.5, color="#102a43")
    for a, b in arrows:
        if a in pos and b in pos:
            x1, y1 = pos[a]; x2, y2 = pos[b]
            ax.add_patch(FancyArrowPatch((x1, y1 - 0.65), (x2, y2 + 0.65),
                         arrowstyle="-|>", mutation_scale=13, color="#334e68", lw=1.3))
    plt.tight_layout()
    path = DIAG / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("SAVED", path.name)


def make_schemes():
    scheme("testing-scheme-1.png", "Схема тестирования SunStay. Часть 1 — уровни",
           ["Требования к системе", "SQL-тесты (БД)", "API-тесты (FastAPI)",
            "UI-тесты (React)", "Интеграционные", "Приёмочные"],
           [(0,1),(0,2),(0,3),(1,4),(2,4),(3,4),(4,5)])
    scheme("testing-scheme-2.png", "Схема тестирования SunStay. Часть 2 — роли",
           ["Гость", "Менеджер", "Хаускипинг", "Управляющий", "Админ БД", "Отчёты и доступы"],
           [(0,5),(1,5),(2,5),(3,5),(4,5)])
    scheme("testing-scheme-3.png", "Схема тестирования SunStay. Часть 3 — качество",
           ["Нагрузочные тесты", "Security-тесты", "RBAC и инъекции",
            "p95 и RPS", "Блокировка входа", "Маскирование данных"],
           [(0,3),(1,2),(1,4),(1,5),(2,4),(2,5)])
    scheme("testing-scheme-4.png", "Схема тестирования SunStay. Часть 4 — надёжность",
           ["pg_dump", "Восстановление БД", "Сверка таблиц", "Сверка броней",
            "Ночной аудит", "Итоговый отчёт"],
           [(0,1),(1,2),(1,3),(2,5),(3,5),(4,5)])


# ---------------------------------------------------------------- UI mockups
ROLE_COLORS = {
    "Гость": "#0b6e4f",
    "Менеджер": "#145da0",
    "Хаускипинг": "#b25e09",
    "Управляющий": "#6a1b9a",
    "Администратор БД": "#8b1e1e",
}


def mock_screen(name, role, screen, rows):
    W, H = 1280, 760
    img = Image.new("RGB", (W, H), "#f4f6f8")
    d = ImageDraw.Draw(img)
    accent = ROLE_COLORS.get(role, "#145da0")
    # browser chrome
    d.rectangle([0, 0, W, 42], fill="#e4e8ec")
    d.text((18, 11), "● ● ●", font=font(15, True), fill="#9aa5b1")
    d.rounded_rectangle([120, 7, W - 20, 35], radius=8, fill="#ffffff")
    d.text((135, 11), "https://sunstay.example/" + screen.lower().replace(" ", "-"), font=font(13), fill="#5b6b7b")
    # header
    d.rectangle([0, 42, W, 108], fill=accent)
    d.text((24, 60), "SunStay", font=font(24, True), fill="white")
    d.text((200, 68), "Система автоматизации гостиницы", font=font(15), fill="#dceaf5")
    d.text((W - 250, 68), "Роль: " + role, font=font(14, True), fill="white")
    # sidebar
    d.rectangle([0, 108, 250, H], fill="#ffffff")
    menu = ["Главная", "Бронирования", "Номера", "Гости", "Счета", "Услуги", "Отчёты", "Настройки"]
    for i, m in enumerate(menu):
        y = 140 + i * 48
        if m in screen or (i == 0 and screen == "Главная"):
            d.rounded_rectangle([12, y - 8, 238, y + 30], radius=6, fill="#e8f1fa")
        d.text((26, y), m, font=font(15), fill="#253746")
    # content title
    d.text((280, 140), screen, font=font(24, True), fill="#1b2a3a")
    d.line([280, 180, W - 30, 180], fill="#d5dce3", width=2)
    # toolbar
    for i, label in enumerate(["Создать", "Фильтр", "Экспорт"]):
        x = 280 + i * 130
        d.rounded_rectangle([x, 200, x + 115, 238], radius=5, fill=accent)
        d.text((x + 18, 209), label, font=font(13, True), fill="white")
    # table
    cols = [300, 620, 880, 1070]
    d.rectangle([280, 262, W - 30, 300], fill=accent)
    heads = ["Наименование", "Значение", "Статус", "Дата"]
    for c, h in zip(cols, heads):
        d.text((c, 272), h, font=font(13, True), fill="white")
    for r in range(rows):
        y = 300 + r * 46
        fill = "#ffffff" if r % 2 == 0 else "#f0f4f7"
        d.rectangle([280, y, W - 30, y + 46], fill=fill, outline="#dde4ea")
        vals = [
            ["Номер 101", "Номер 205", "Тариф Стандарт", "Гость demo", "Бронь 1042", "Услуга «Завтрак»"][r % 6],
            ["SunStay De Luxe", "8 900 ₽ / сутки", "2 гостя", "sokolova.demo", "22.11 — 01.12", "450 ₽"][r % 6],
            ["Свободен", "Подтверждён", "Готов", "Заселён", "Оплачен", "Выполнено"][r % 6],
            ["22.11.2026", "23.11.2026", "24.11.2026", "25.11.2026", "26.11.2026", "27.11.2026"][r % 6],
        ]
        for c, v in zip(cols, vals):
            d.text((c, y + 13), v, font=font(12), fill="#253746")
    d.text((280, H - 34), "SunStay © 2026 — тестовые данные", font=font(11), fill="#8b98a5")
    path = SHOTS / name
    img.save(path)
    print("SAVED", path.name)


def make_shots():
    screens = [
        ("sst-guest-home.png", "Гость", "Главная", 5),
        ("sst-guest-search.png", "Гость", "Поиск номеров", 5),
        ("sst-guest-room.png", "Гость", "Карточка номера", 4),
        ("sst-guest-booking.png", "Гость", "Мои брони", 5),
        ("sst-guest-folio.png", "Гость", "Счета и платежи", 4),
        ("sst-guest-services.png", "Гость", "Заказ услуг", 5),
        ("sst-guest-reviews.png", "Гость", "Отзывы", 4),
        ("sst-guest-profile.png", "Гость", "Профиль и 2FA", 4),
        ("sst-manager-dashboard.png", "Менеджер", "Дашборд", 5),
        ("sst-manager-bookings.png", "Менеджер", "Бронирования", 6),
        ("sst-manager-grid.png", "Менеджер", "Шахматка", 5),
        ("sst-manager-checkin.png", "Менеджер", "Заселение", 5),
        ("sst-manager-folio.png", "Менеджер", "Folio и платежи", 5),
        ("sst-manager-waitlist.png", "Менеджер", "Лист ожидания", 4),
        ("sst-manager-reports.png", "Менеджер", "Отчёты", 5),
        ("sst-hk-board.png", "Хаускипинг", "Доска заданий", 5),
        ("sst-hk-task.png", "Хаускипинг", "Выполнение задания", 4),
        ("sst-hk-stock.png", "Хаускипинг", "Расходники", 5),
        ("sst-hk-repair.png", "Хаускипинг", "Заявка на ремонт", 4),
        ("sst-mgr-ref.png", "Управляющий", "Справочники", 5),
        ("sst-mgr-staff.png", "Управляющий", "Сотрудники", 5),
        ("sst-mgr-audit.png", "Управляющий", "Журнал аудита", 5),
        ("sst-dba-users.png", "Администратор БД", "Пользователи и роли", 5),
        ("sst-dba-backup.png", "Администратор БД", "Резервное копирование", 4),
        ("sst-dba-monitor.png", "Администратор БД", "Мониторинг", 4),
    ]
    for a, b, c, d in screens:
        mock_screen(a, b, c, d)


if __name__ == "__main__":
    make_schemes()
    make_shots()
