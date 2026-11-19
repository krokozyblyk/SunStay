import json, urllib.request, urllib.error
BASE = "http://localhost:8000/api"

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
status, avail = req("GET", "/public/availability?checkin=2026-12-20&checkout=2026-12-22&guests=2")
room = avail[0]["rooms"][0]
print("AMENITIES", room.get("amenities"))
status, folios = req("GET", "/manager/folios?status=OPEN&page_size=3", headers=auth)
items = folios.get("items", []) if isinstance(folios, dict) else []
if items:
    ids = [f["folio_id"] for f in items[:2]]
    status, res = req("POST", "/manager/folios/bulk-close", {"folio_ids": ids}, headers=auth)
    print("BULK CLOSE", status, res)
