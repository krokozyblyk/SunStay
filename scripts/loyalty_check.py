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

status, login = req("POST", "/auth/login", {"email": "manager", "password": "x"})
status, login = req("POST", "/auth/login", {"email": "smirnova@sunstay.example", "password": "SunStay2026!"})
auth = {"Authorization": "Bearer " + login["access_token"]}
status, folios = req("GET", "/manager/folios?status=OPEN&page_size=10", headers=auth)
items = folios.get("items", []) if isinstance(folios, dict) else []
print("FOLIOS", status, len(items))
if items:
    f = items[0]
    print("PICK", f["folio_id"], f["booking_id"], f.get("guest_name"))
    status, res = req("POST", f"/manager/folios/{f['folio_id']}/close", headers=auth)
    print("CLOSE", status, res)
