"""Generate additional SunStay diagrams as PNG for the PZ."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parents[1] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def boxes(title, items, arrows, name, cols=3):
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", pad=12)
    pos = {}
    step_x = 12 / (cols + 1)
    for i, text in enumerate(items):
        r, c = divmod(i, cols)
        x = step_x * (c + 1)
        y = 6.2 - r * 2.3
        pos[i] = (x, y)
        box = FancyBboxPatch((x - 1.6, y - 0.55), 3.2, 1.1,
                             boxstyle="round,pad=0.12", facecolor="#e3f2fd",
                             edgecolor="#1a237e", linewidth=1.6)
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", fontsize=10, color="#0d1b4c")
    for a, b in arrows:
        if a in pos and b in pos:
            x1, y1 = pos[a]; x2, y2 = pos[b]
            ax.add_patch(FancyArrowPatch((x1, y1 - 0.6), (x2, y2 + 0.6),
                         arrowstyle="-|>", mutation_scale=14, color="#1565c0", lw=1.4))
    plt.tight_layout()
    path = OUT / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("SAVED", path.name)


def main():
    boxes("Архитектура потоков данных SunStay",
          ["Клиент (React SPA)", "Nginx", "Core API (FastAPI)", "Analytics API",
           "PostgreSQL 16", "Планировщик", "Хранилище бэкапов"],
          [(0, 1), (1, 2), (1, 3), (2, 4), (3, 4), (2, 5), (2, 6)],
          "dataflow.png", cols=3)

    boxes("Процесс бронирования и заселения",
          ["Поиск доступности", "Выбор номера", "Создание брони", "Подтверждение",
           "Заселение", "Folio и услуги", "Выселение", "Закрытие счёта", "Начисление бонусов"],
          [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8)],
          "booking-flow.png", cols=3)

    boxes("Диаграмма состояний номера",
          ["Свободен", "Готов", "Бронирован", "Заселён", "Грязный", "Заблокирован"],
          [(0, 1), (1, 2), (2, 3), (3, 4), (4, 1), (0, 5), (5, 1)],
          "room-states.png", cols=3)

    boxes("Компоненты системы SunStay",
          ["React SPA", "FastAPI core", "FastAPI analytics", "PostgreSQL",
           "Nginx", "Docker Compose", "pg_dump/restore", "GitHub Actions"],
          [(0, 4), (4, 1), (4, 2), (1, 3), (2, 3), (5, 0), (5, 1), (6, 3), (7, 6)],
          "components.png", cols=3)

    boxes("Схема тестирования SunStay",
          ["SQL-тесты", "API-тесты", "Интеграционные", "Нагрузочные",
           "Security-тесты", "Playwright E2E", "Тест restore", "Приёмочные"],
          [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)],
          "testing-flow.png", cols=3)


if __name__ == "__main__":
    main()
