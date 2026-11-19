import json, urllib.request, urllib.error, sys, uuid
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000") + "/api"

def req(method, path, data=None, headers=None):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Content-Type": "application/json"}
    if headers: h.update(headers)
    r = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

status, login = req("POST", "/auth/login", {"email": "guest.demo@sunstay.example", "password": "SunStay2026!"})
auth = {"Authorization": "Bearer " + login["access_token"]}
status, avail = req("GET", "/public/availability?checkin=2026-12-20&checkout=2026-12-22&guests=2")
room = avail[0]["rooms"][0]
print("PICK", room["room_id"], room.get("rate_id"))
status, booking = req("POST", "/public/bookings", {
    "full_name": "Live Smoke", "document_number": "4510 999888",
    "phone": "+7 900 111-22-33", "email": "smoke@sunstay.example",
    "pdn_consent": True, "payment_method": "ONLINE", "arrival_time": "14:00",
    "hold_minutes": 60, "special_requests": "",
    "room_id": room["room_id"], "rate_id": room.get("rate_id"),
    "checkin_date": "2026-12-20", "checkout_date": "2026-12-22",
    "adults": 2, "children": 0, "source": "SITE", "points_to_use": 0,
}, headers={**auth, "Idempotency-Key": str(uuid.uuid4())})
print("BOOK", status, booking if status != 200 else booking.get("booking_id"))
