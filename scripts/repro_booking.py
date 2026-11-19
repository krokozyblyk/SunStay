import json, urllib.request, urllib.error, sys

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000") + "/api"

def req(method, path, data=None, headers=None):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

status, login = req("POST", "/auth/login", {
    "email": "guest.demo@sunstay.example",
    "password": "SunStay2026!",
})
print("LOGIN", status, login if status != 200 else "ok")
if status != 200:
    raise SystemExit(1)
token = login["access_token"]
auth = {"Authorization": f"Bearer {token}"}

status, avail = req("GET", "/public/availability?checkin=2026-12-20&checkout=2026-12-22&guests=2")
print("AVAIL", status, json.dumps(avail, ensure_ascii=False)[:600] if status == 200 else avail)
if status != 200:
    raise SystemExit(1)

rt = avail[0]
room = rt["rooms"][0]
print("PICK", rt["name"], room["room_id"], room.get("rate_id"), room.get("price_per_night"))

status, booking = req("POST", "/public/bookings", {
    "full_name": "Тест Гость",
    "document_number": "4510 123456",
    "phone": "+7 900 111-22-33",
    "email": "test@example.com",
    "pdn_consent": True,
    "payment_method": "ONLINE",
    "arrival_time": "14:00",
    "hold_minutes": 60,
    "special_requests": "",
    "room_id": room["room_id"],
    "rate_id": room.get("rate_id"),
    "checkin_date": "2026-12-20",
    "checkout_date": "2026-12-22",
    "adults": 2,
    "children": 0,
    "source": "SITE",
    "points_to_use": 0,
}, headers={**auth, "Idempotency-Key": "repro-002"})
print("BOOK", status, json.dumps(booking, ensure_ascii=False)[:800])
