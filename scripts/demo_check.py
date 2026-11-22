import json, urllib.request, urllib.error, sys
BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://sunstay-api.onrender.com") + "/api"

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

for email in ["sokolova.demo@sunstay.example", "belov.demo@sunstay.example", "morozova.hk@sunstay.example"]:
    status, login = req("POST", "/auth/login", {"email": email, "password": "SunStay2026!"})
    if status != 200 or "access_token" not in login:
        print("FAIL LOGIN", email, status, str(login)[:200]); continue
    auth = {"Authorization": "Bearer " + login["access_token"]}
    role = login["user"].get("role_code")
    print("PASS LOGIN", email, role)
    if role == "GUEST":
        status, bookings = req("GET", "/guest/bookings", headers=auth)
        items = bookings if isinstance(bookings, list) else bookings.get("items", [])
        print("  BOOKINGS", status, [(b.get("booking_id"), b.get("status"), b.get("checkin_date"), b.get("checkout_date")) for b in items])
    else:
        status, notes = req("GET", "/notifications?limit=5", headers=auth)
        print("  NOTIFICATIONS", status, [n.get("notification_type") for n in notes] if isinstance(notes, list) else str(notes)[:150])
        if role == "HOUSEKEEPING":
            status, tasks = req("GET", "/housekeeping/tasks", headers=auth)
            print("  TASKS", status, len(tasks) if isinstance(tasks, list) else str(tasks)[:150])
