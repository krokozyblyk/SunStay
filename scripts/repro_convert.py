import json, urllib.request, urllib.error, sys
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

status, login = req("POST", "/auth/login", {"email": "smirnova@sunstay.example", "password": "SunStay2026!"})
print("LOGIN", status)
auth = {"Authorization": "Bearer " + login["access_token"]}
status, wl = req("POST", "/public/waitlist", {
    "full_name": "Convert Test", "email": "convert@test.example", "phone": "+7 900 222-33-44",
    "room_type_id": 1, "checkin_date": "2026-12-20", "checkout_date": "2026-12-22",
    "adults": 2, "children": 0, "note": "convert repro",
})
print("WL", status, str(wl)[:200])
wid = wl.get("waitlist_id")
status, availability = req("GET", "/public/availability?checkin=2026-12-20&checkout=2026-12-22&guests=2")
room = availability[0]["rooms"][0]
print("ROOM", room["room_id"], room.get("capacity"))
status, rates = req("GET", "/manager/rates", headers=auth)
rate = next(r for r in rates if r["room_type_id"] == 1)
print("RATE", rate["rate_id"])
status, result = req("POST", f"/manager/waitlist/{wid}/convert", {
    "room_id": room["room_id"], "rate_id": rate["rate_id"], "document_number": "1234 567890",
}, headers=auth)
print("CONVERT", status, str(result)[:600])
