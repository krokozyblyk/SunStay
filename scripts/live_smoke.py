"""Live smoke test for SunStay API. Runs from GitHub Actions (no VPN needed)."""
import json
import urllib.request
import urllib.error
import uuid

BASE = "https://sunstay-api.onrender.com/api"
PASS = "PASS"
FAIL = "FAIL"


def req(method, path, data=None, headers=None, timeout=120):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)


def check(name, cond, detail=""):
    print(f"{PASS if cond else FAIL} {name} {detail}", flush=True)


def login(email, password):
    status, data = req("POST", "/auth/login", {"email": email, "password": password})
    if status == 200 and "access_token" in data:
        return {"Authorization": f"Bearer {data['access_token']}"}
    print(f"FAIL login {email}: {status} {str(data)[:200]}", flush=True)
    return None


PW = "SunStay2026!"
guest = login("guest.demo@sunstay.example", PW)
dba = login("dba@sunstay.example", PW)
manager = login("smirnova@sunstay.example", PW)
check("logins (guest/dba/manager)", bool(guest and dba and manager))

# Feature flags
status, cfg = req("GET", "/public/config")
check("public config", status == 200 and cfg.get("features", {}).get("reviews") is True, str(cfg)[:200])

# Room detail
status, room = req("GET", "/public/rooms/9")
check("room detail", status == 200 and room.get("room_type") == "Стандарт", str(room)[:200])

# Booking (the previously failing flow)
status, avail = req("GET", "/public/availability?checkin=2026-12-20&checkout=2026-12-22&guests=2")
if status == 200 and avail:
    room = avail[0]["rooms"][0]
    status, booking = req("POST", "/public/bookings", {
        "full_name": "Live Smoke", "document_number": "4510 999888",
        "phone": "+7 900 111-22-33", "email": "smoke@sunstay.example",
        "pdn_consent": True, "payment_method": "ONLINE", "arrival_time": "14:00",
        "hold_minutes": 60, "special_requests": "",
        "room_id": room["room_id"], "rate_id": room.get("rate_id"),
        "checkin_date": "2026-12-20", "checkout_date": "2026-12-22",
        "adults": 2, "children": 0, "source": "SITE", "points_to_use": 0,
    }, headers={**(guest or {}), "Idempotency-Key": str(uuid.uuid4())})
    check("create booking", status == 200 and booking.get("booking_id"), f"{status} {str(booking)[:200]}")
else:
    check("availability", False, str(avail)[:200])

# 2FA status
status, twofa = req("GET", "/auth/2fa/status", headers=guest)
check("2fa status", status == 200 and "enabled" in twofa, str(twofa)[:200])

# Hotel review published instantly
status, review = req("POST", "/guest/reviews", {
    "rating": 5, "title": "Live smoke", "body": "Отличный отель, рекомендую!"
}, headers=guest)
check("hotel review instant", status == 200 and review.get("status") == "APPROVED", f"{status} {str(review)[:200]}")
status, reviews = req("GET", "/public/reviews?limit=5")
check("public reviews visible", status == 200 and any(r.get("title") == "Live smoke" for r in reviews), str(reviews)[:200])

# Backups
status, created = req("POST", "/admin/backups", headers=dba)
check("backup create", status == 200 and isinstance(created, dict) and created.get("size", 0) > 0, f"{status} {str(created)[:250]}")
status, backups = req("GET", "/admin/backups", headers=dba)
file_info = (backups or {}).get("file") or {} if isinstance(backups, dict) else {}
check("backups list", status == 200 and file_info.get("size", 0) > 0, f"{status} {str(backups)[:250]}")
if file_info.get("size", 0) > 0:
    status, verify = req("POST", "/admin/backups/verify", headers=dba)
    check("backup verify", status == 200 and isinstance(verify, dict) and verify.get("ok") is True, f"{status} {str(verify)[:250]}")
    status, restore = req("POST", "/admin/backups/test-restore", headers=dba)
    check("backup test-restore", status == 200 and isinstance(restore, dict) and restore.get("ok") is True, f"{status} {str(restore)[:350]}")

# Waitlist notified -> guest notification
status, wl = req("POST", "/public/waitlist", {
    "full_name": "Guest Demo", "email": "guest.demo@sunstay.example",
    "phone": "+7 900 111-22-33", "room_type_id": 1,
    "checkin_date": "2026-12-20", "checkout_date": "2026-12-22",
    "adults": 2, "children": 0, "note": "live smoke",
}, headers=guest)
check("waitlist create", status in (200, 201), f"{status} {str(wl)[:200]}")
if status in (200, 201) and wl.get("waitlist_id"):
    status, updated = req("PATCH", f"/manager/waitlist/{wl['waitlist_id']}", {"status": "NOTIFIED"}, headers=manager)
    check("waitlist notify", status == 200, f"{status} {str(updated)[:200]}")
    status, notes = req("GET", "/notifications?limit=10", headers=guest)
    found = any(n.get("notification_type") == "WAITLIST" for n in (notes if isinstance(notes, list) else []))
    check("guest got WAITLIST notification", status == 200 and found, str(notes)[:300])

    # Convert a fresh waitlist entry into a booking
    status, wl2 = req("POST", "/public/waitlist", {
        "full_name": "Convert Smoke", "email": "guest.demo@sunstay.example",
        "phone": "+7 900 111-22-33", "room_type_id": 1,
        "checkin_date": "2026-12-20", "checkout_date": "2026-12-22",
        "adults": 2, "children": 0, "note": "convert smoke",
    }, headers=guest)
    if status in (200, 201) and wl2.get("waitlist_id"):
        status, rooms = req("GET", "/public/availability?checkin=2026-12-20&checkout=2026-12-22&guests=2")
        room = rooms[0]["rooms"][0] if rooms and rooms[0].get("rooms") else None
        status, rates = req("GET", "/manager/rates", headers=manager)
        rate = next((r for r in rates if r["room_type_id"] == 1), None) if isinstance(rates, list) else None
        if room and rate:
            status, conv = req("POST", f"/manager/waitlist/{wl2['waitlist_id']}/convert", {
                "room_id": room["room_id"], "rate_id": rate["rate_id"],
                "document_number": "9988776655",
            }, headers=manager)
            check("waitlist convert to booking", status == 200 and conv.get("booking_id"), f"{status} {str(conv)[:200]}")

print("LIVE SMOKE DONE", flush=True)
