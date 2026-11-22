"""Seed extra demo users/bookings into Supabase so the site looks populated."""
from pathlib import Path
import hashlib
import re
import time
import bcrypt
from cryptography.fernet import Fernet
import psycopg

env = {}
for line in Path(".env.deploy").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

URL = env["DATABASE_ADMIN_URL"]
KEY = env["DATA_ENCRYPTION_KEY"].encode()
fernet = Fernet(KEY)
PASSWORD_HASH = bcrypt.hashpw(b"SunStay2026!", bcrypt.gensalt(rounds=12)).decode()


def connect():
    return psycopg.connect(URL, options="-c search_path=public,extensions", autocommit=True)


def run(sql, params=None, fetch="one"):
    """Execute with fresh connection + retry (Supabase pooler drops idle conns)."""
    last = None
    for attempt in range(6):
        try:
            with connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params or ())
                    try:
                        if fetch == "one":
                            return cur.fetchone()
                        if fetch == "all":
                            return cur.fetchall()
                    except psycopg.ProgrammingError:
                        return None
                    return None
        except psycopg.OperationalError as e:
            last = e
            time.sleep(0.8 * (attempt + 1))
    raise last


def norm_phone(v):
    return re.sub(r"\D", "", v or "")


def norm_doc(v):
    return re.sub(r"\s+", "", v or "").upper()


def h(v):
    return hashlib.sha256(v.encode()).hexdigest() if v else None


def enc(v):
    return fernet.encrypt(v.encode()).decode() if v else None


def mask_phone(v):
    d = norm_phone(v)
    return f"+7 ***-**-{d[-2:]}" if len(d) > 2 else "+7 ***-**-**"


def mask_doc(v):
    n = norm_doc(v)
    return f"**** {n[-4:]}" if len(n) > 4 else "****"


def phone_fields(v):
    return mask_phone(v), enc(v), h(norm_phone(v))


def doc_fields(v):
    return mask_doc(v), enc(v), h(norm_doc(v))


def make_user(email, name, role_id, phone, doc=None):
    row = run("SELECT user_id FROM users WHERE lower(email)=lower(%s)", (email,))
    if row:
        uid = row[0]
        print("USER EXISTS", email, uid, flush=True)
        if doc and not run("SELECT 1 FROM guests WHERE user_id=%s", (uid,)):
            dm, de, dh = doc_fields(doc)
            ph, phe, phh = phone_fields(phone)
            run(
                """INSERT INTO guests (full_name, phone, email, pdn_consent, user_id,
                   phone_enc, phone_hash, document_number, document_number_enc, document_number_hash)
                   VALUES (%s,%s,%s,TRUE,%s,%s,%s,%s,%s,%s) RETURNING guest_id""",
                (name, ph, email, uid, phe, phh, dm, de, dh),
            )
            print("GUEST CREATED FOR EXISTING USER", name, flush=True)
        return uid
    ph, phe, phh = phone_fields(phone)
    row = run(
        """INSERT INTO users (role_id, full_name, email, phone, password_hash,
           phone_enc, phone_hash, is_active)
           VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE) RETURNING user_id""",
        (role_id, name, email, ph, PASSWORD_HASH, phe, phh),
    )
    uid = row[0]
    print("USER CREATED", email, uid, flush=True)
    if doc:
        dm, de, dh = doc_fields(doc)
        row = run(
            """INSERT INTO guests (full_name, phone, email, pdn_consent, user_id,
               phone_enc, phone_hash, document_number, document_number_enc, document_number_hash)
               VALUES (%s,%s,%s,TRUE,%s,%s,%s,%s,%s,%s) RETURNING guest_id""",
            (name, ph, email, uid, phe, phh, dm, de, dh),
        )
        print("GUEST CREATED", name, row[0], flush=True)
    return uid


def guest_id_for(user_id):
    row = run("SELECT guest_id FROM guests WHERE user_id=%s", (user_id,))
    return row[0] if row else None


def free_room(checkin, checkout):
    row = run(
        """SELECT r.room_id FROM rooms r
           JOIN room_types rt ON rt.room_type_id = r.room_type_id
           WHERE rt.name = 'Стандарт'
             AND NOT EXISTS (
               SELECT 1 FROM bookings b
               WHERE b.room_id = r.room_id
                 AND b.status NOT IN ('CANCELLED','NO_SHOW')
                 AND b.checkin_date < %s AND b.checkout_date > %s
             ) AND fn_room_available(r.room_id, %s, %s)
           ORDER BY r.room_id LIMIT 1""",
        (checkout, checkin, checkin, checkout),
    )
    return row[0] if row else None


def main():
    hk = make_user("morozova.hk@sunstay.example", "Морозова Ирина Павловна", 3, "+7 921 777-88-99")
    g1 = make_user("sokolova.demo@sunstay.example", "Соколова Елена Викторовна", 1,
                   "+7 916 222-33-44", "4510 778899")
    g2 = make_user("belov.demo@sunstay.example", "Белов Артём Сергеевич", 1,
                   "+7 903 444-55-66", "4510 445566")

    gid1 = guest_id_for(g1)
    if gid1 and not run("SELECT 1 FROM bookings WHERE guest_id=%s AND checkin_date=DATE '2026-11-22'", (gid1,)):
        room = free_room("2026-11-22", "2026-12-01")
        bid = run(
            """SELECT fn_create_booking(%s,%s,5,DATE '2026-11-22',DATE '2026-12-01',
               NULL,'SITE',2,0,NULL,'127.0.0.1','14:00',60)""",
            (gid1, room),
        )[0]
        run("UPDATE bookings SET status='CHECKED_IN', special_requests='Ранний заезд, тихий этаж' WHERE booking_id=%s", (bid,))
        fid = run("""INSERT INTO folios (booking_id,status,opened_at)
                     VALUES (%s,'OPEN',TIMESTAMP '2026-11-22 14:10:00') RETURNING folio_id""", (bid,))[0]
        run("""INSERT INTO folio_lines (folio_id,description,amount,line_type,charge_date)
               VALUES (%s,'Проживание 22.11 — 01.12',45000,'ROOM',DATE '2026-11-22')""", (fid,))
        run("""INSERT INTO check_ins (booking_id,manager_id,guest_document_number,
               guest_document_number_enc,guest_document_number_hash,actual_checkin_at)
               VALUES (%s,2,'**** 8899',%s,%s,TIMESTAMP '2026-11-22 14:10:00')""",
            (bid, enc("4510 778899"), h(norm_doc("4510 778899"))))
        run("UPDATE rooms SET status_id=(SELECT status_id FROM room_statuses WHERE name='ЗАСЕЛЁН') WHERE room_id=%s", (room,))
        print("CHECKED-IN BOOKING", bid, "room", room, flush=True)

    gid2 = guest_id_for(g2)
    if gid2 and not run("SELECT 1 FROM bookings WHERE guest_id=%s AND checkin_date=DATE '2026-11-25'", (gid2,)):
        room = free_room("2026-11-25", "2026-11-28")
        bid = run(
            """SELECT fn_create_booking(%s,%s,5,DATE '2026-11-25',DATE '2026-11-28',
               NULL,'SITE',1,0,NULL,'127.0.0.1','15:00',60)""",
            (gid2, room),
        )[0]
        run("UPDATE bookings SET status='CONFIRMED', special_requests='Высокий этаж, если возможно' WHERE booking_id=%s", (bid,))
        print("UPCOMING BOOKING", bid, "room", room, flush=True)

    if hk and not run("SELECT 1 FROM housekeeping_tasks WHERE staff_id=%s", (hk,)):
        rr = run("""SELECT r.room_id FROM rooms r JOIN room_statuses s ON s.status_id=r.status_id
                    WHERE s.name='ГОТОВ' ORDER BY r.room_id LIMIT 1""")
        if rr:
            run("""INSERT INTO housekeeping_tasks (room_id,staff_id,task_type,status,priority)
                   VALUES (%s,%s,'POST_CHECKOUT','ASSIGNED','HIGH')""", (rr[0], hk))
            print("TASK CREATED room", rr[0], flush=True)


if __name__ == "__main__":
    main()
