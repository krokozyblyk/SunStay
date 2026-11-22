"""Assign the 55 unique St Petersburg hotel-room photos to the 55 rooms."""
import sys
sys.path.insert(0, "scripts")
from seed_demo_users import run

BASE = "images/spb/"

GROUPS = {
    "Стандарт::Классика": [f"standard-classic-{i}.jpg" for i in range(1, 9)] + [f"standard-cozy-{i}.jpg" for i in range(1, 6)],
    "Стандарт::Панорама": [f"standard-panorama-{i}.jpg" for i in range(1, 9)] + [f"standard-cozy-{i}.jpg" for i in range(6, 8)],
    "Стандарт::": [f"standard-cozy-{i}.jpg" for i in range(8, 9)],

    "Комфорт::Городской вид": [f"comfort-city-{i}.jpg" for i in range(1, 9)] + [f"comfort-business-{i}.jpg" for i in range(3, 5)],
    "Комфорт::Простор": [f"comfort-spacious-{i}.jpg" for i in range(1, 8)] + [f"comfort-business-{i}.jpg" for i in range(5, 8)],
    "Комфорт::Бизнес": [f"comfort-business-{i}.jpg" for i in range(1, 3)],

    "Люкс::Классик": [f"lux-classic-{i}.jpg" for i in range(1, 4)],
    "Люкс::Панорамный": [f"lux-panorama-{i}.jpg" for i in range(1, 4)] + [f"lux-president-{i}.jpg" for i in range(1, 3)],
    "Люкс::Президентский": [f"lux-president-{i}.jpg" for i in range(3, 4)],
}


def main():
    rooms = run("""SELECT r.room_id, rt.name, COALESCE(r.variant_name,'')
                   FROM rooms r JOIN room_types rt ON rt.room_type_id=r.room_type_id
                   ORDER BY rt.name, r.variant_name, r.room_id""", fetch="all")
    used = set()
    assigned = 0
    for room_id, type_name, variant in rooms:
        key = f"{type_name}::{variant}"
        pool = GROUPS.get(key)
        if not pool:
            print("NO POOL", key)
            continue
        pick = next((f for f in pool if f not in used), None)
        if not pick:
            print("POOL EXHAUSTED", key)
            continue
        run("UPDATE rooms SET image_url=%s WHERE room_id=%s", (BASE + pick, room_id))
        used.add(pick)
        assigned += 1
    print("ASSIGNED", assigned, "UNIQUE", len(used))


if __name__ == "__main__":
    main()
