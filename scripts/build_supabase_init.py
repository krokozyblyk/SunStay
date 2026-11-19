from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "000_extensions.sql",
    "001_hotel_db.sql",
    "002_week5.sql",
    "003_week6.sql",
    "004_week8_views.sql",
    "006_fix_checkout.sql",
    "007_demo_current.sql",
    "008_security_features.sql",
    "008b_audit_function.sql",
    "009_encryption.sql",
    "010_secure_checkin_hold.sql",
    "011_closed_day_fix.sql",
    "012_guest_experience.sql",
    "013_loyalty_security.sql",
    "014_guest_cancellation.sql",
]

parts = [
    "-- SunStay: единый скрипт инициализации для Supabase/PostgreSQL.\n"
    "-- Роли БД (005_db_roles.sql) намеренно пропущены: используется пользователь postgres.\n"
]
for name in FILES:
    path = ROOT / "database" / "init" / name
    parts.append(f"\n-- ===== {name} =====\n")
    parts.append(path.read_text(encoding="utf-8"))

(ROOT / "database" / "supabase_init.sql").write_text("".join(parts), encoding="utf-8")
print("database/supabase_init.sql written")
