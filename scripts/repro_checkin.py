import json, urllib.request, urllib.error, sys
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000") + "/api"

def req(method, path, data=None, headers=None):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Content-Type": "application/json"}
    if headers: h.update(headers)
    r = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

status, login = req("POST", "/auth/login", {"email": "smirnova@sunstay.example", "password": "SunStay2026!"})
auth = {"Authorization": "Bearer " + login["access_token"]}
status, bookings = req("GET", "/manager/bookings?status=CONFIRMED&page_size=5", headers=auth)
items = bookings.get("items", []) if isinstance(bookings, dict) else []
print("BOOKINGS", status, len(items))
if items:
    b = items[0]
    print("PICK", b.get("booking_id"), b.get("status"), b.get("document_number"))
    for doc in [b.get("document_number") or "**** 3456", ""]:
        status, res = req("POST", f"/manager/bookings/{b['booking_id']}/check-in", {
            "document_number": doc, "deposit_amount": 0, "payment_method": "CARD"
        }, headers=auth)
        print("CHECKIN doc=", repr(doc), status, str(res)[:250])
