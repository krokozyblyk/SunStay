import json, urllib.request, urllib.error, sys

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000") + "/api"

def req(method, path, data=None, headers=None):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(BASE + path, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, f"<binary {len(raw)} chars>"
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

status, login = req("POST", "/auth/login", {
    "email": "dba@sunstay.example", "password": "SunStay2026!"
})
print("LOGIN", status)
token = login["access_token"]
auth = {"Authorization": f"Bearer {token}"}

for path, method in [
    ("/admin/backups", "GET"),
    ("/admin/backups/verify", "POST"),
    ("/admin/backups/test-restore", "POST"),
    ("/admin/backups", "POST"),
    ("/admin/backups/download", "GET"),
]:
    status, result = req(method, path, headers=auth)
    print(method, path, status, json.dumps(result, ensure_ascii=False)[:500])
