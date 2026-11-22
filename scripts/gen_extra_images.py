"""Generate four clean, large SunStay testing-scheme diagrams for appendix В."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "docs" / "diagrams"
DIAG.mkdir(parents=True, exist_ok=True)


def scheme(name, title, items, arrows):
    """Two tidy rows of boxes. arrows: (from, to, 'h'|'v')."""
    fig, ax = plt.subplots(figsize=(18, 8))
    ax.set_xlim(0, 12); ax.set_ylim(1.2, 8.2); ax.axis("off")
    ax.set_title(title, fontsize=22, fontweight="bold", pad=16)

    pos = {}
    for i, text in enumerate(items):
        row, col = divmod(i, 3)
        x = 2.0 + col * 4.0
        y = 6.2 - row * 2.6
        pos[i] = (x, y)
        fc = "#e8f2fb" if row == 0 else "#eaf6ee"
        ec = "#155e9e" if row == 0 else "#237a3f"
        box = FancyBboxPatch((x - 1.75, y - 0.62), 3.5, 1.24,
                             boxstyle="round,pad=0.12", facecolor=fc,
                             edgecolor=ec, linewidth=2.2)
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", fontsize=13, color="#12263a")

    for a, b, kind in arrows:
        if a not in pos or b not in pos:
            continue
        x1, y1 = pos[a]; x2, y2 = pos[b]
        if kind == "h":
            start = (x1 + 1.78, y1)
            end = (x2 - 1.88, y2)
            conn = "arc3,rad=0"
        else:
            start = (x1, y1 - 0.66)
            end = (x2, y2 + 0.66)
            conn = "arc3,rad=0"
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>",
                     mutation_scale=18, color="#334e68", lw=2.0,
                     connectionstyle=conn))

    fig.subplots_adjust(top=0.90, bottom=0.06, left=0.02, right=0.98)
    fig.savefig(DIAG / name, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("SAVED", name)


def main():
    scheme("testing-scheme-1.png", "Схема тестирования SunStay. Часть 1 — уровни",
           ["Требования к системе", "SQL-тесты базы данных", "API-тесты FastAPI",
            "UI-тесты React", "Интеграционные тесты", "Приёмочные тесты"],
           [(0, 1, "h"), (1, 2, "h"), (2, 5, "v"), (3, 4, "h"), (4, 5, "h")])
    scheme("testing-scheme-2.png", "Схема тестирования SunStay. Часть 2 — роли",
           ["Гость", "Менеджер", "Хаускипинг", "Управляющий отелем",
            "Администратор БД", "Итоговая оценка"],
           [(0, 1, "h"), (1, 2, "h"), (3, 4, "h"), (4, 5, "h"), (2, 5, "v")])
    scheme("testing-scheme-3.png", "Схема тестирования SunStay. Часть 3 — качество",
           ["Нагрузочные тесты", "Security-тесты", "Проверка RBAC",
            "Замеры p95 и RPS", "Блокировка входа", "Маскирование данных"],
           [(0, 1, "h"), (1, 2, "h"), (3, 4, "h"), (4, 5, "h"), (2, 5, "v")])
    scheme("testing-scheme-4.png", "Схема тестирования SunStay. Часть 4 — надёжность",
           ["Создание pg_dump", "Восстановление БД", "Сверка таблиц",
            "Сверка бронирований", "Ночной аудит", "Итоговый отчёт"],
           [(0, 1, "h"), (1, 2, "h"), (3, 4, "h"), (4, 5, "h"), (2, 5, "v")])


if __name__ == "__main__":
    main()
