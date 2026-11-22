"""Generate the four enlarged SunStay testing-scheme diagrams for appendix В.

Real UI screenshots are captured from the deployed site (collect_real_shots.py),
so this script only creates diagrams.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "docs" / "diagrams"
DIAG.mkdir(parents=True, exist_ok=True)


def scheme(name, title, items, arrows):
    fig, ax = plt.subplots(figsize=(20, 12))
    ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis("off")
    ax.set_title(title, fontsize=24, fontweight="bold", pad=24)
    pos = {}
    for i, text in enumerate(items):
        r, c = divmod(i, 3)
        x = 2 + c * 4
        y = 6.2 - r * 2.0
        pos[i] = (x, y)
        fc = "#e8f4fd" if i % 2 == 0 else "#eaf7ee"
        ec = "#145da0" if i % 2 == 0 else "#1b7a3d"
        box = FancyBboxPatch((x - 1.85, y - 0.72), 3.7, 1.44,
                             boxstyle="round,pad=0.16", facecolor=fc,
                             edgecolor=ec, linewidth=2.6)
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", fontsize=14, color="#102a43")
    for a, b in arrows:
        if a in pos and b in pos:
            x1, y1 = pos[a]; x2, y2 = pos[b]
            ax.add_patch(FancyArrowPatch((x1, y1 - 0.78), (x2, y2 + 0.78),
                         arrowstyle="-|>", mutation_scale=20, color="#334e68", lw=2.2))
    plt.tight_layout()
    fig.savefig(DIAG / name, dpi=170, bbox_inches="tight")
    plt.close(fig)
    print("SAVED", name)


def main():
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


if __name__ == "__main__":
    main()
