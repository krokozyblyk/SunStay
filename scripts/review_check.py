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

for email in ["guest.demo@sunstay.example", "smirnova@sunstay.example", "dba@sunstay.example"]:
    status, login = req("POST", "/auth/login", {"email": email, "password": "SunStay2026!"})
    if status != 200 or "access_token" not in login:
        print("LOGIN FAIL", email, status, str(login)[:150]); continue
    auth = {"Authorization": "Bearer " + login["access_token"]}
    status, result = req("POST", "/public/hotel-reviews", {"rating": 5, "title": "Проверка", "body": "Отличный отель и приветливый персонал!"}, headers=auth)
    print("REVIEW", email, status, str(result)[:200])
