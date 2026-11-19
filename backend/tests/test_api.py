from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def login(client: TestClient, email: str, password: str = "SunStay2026!") -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_manager_dashboard() -> None:
    with TestClient(app) as client:
        session = login(client, "smirnova@sunstay.example")
        response = client.get("/api/manager/dashboard", headers=auth_headers(session["access_token"]))
        assert response.status_code == 200
        data = response.json()
        assert "kpi" in data
        assert "occupancy" in data
        assert data["kpi"]["total_rooms"] >= 6


def test_public_availability_and_booking_list() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/public/availability",
            params={"checkin": "2026-12-20", "checkout": "2026-12-22", "guests": 2},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_guest_cannot_access_manager_api() -> None:
    with TestClient(app) as client:
        session = login(client, "guest.demo@sunstay.example")
        response = client.get("/api/manager/dashboard", headers=auth_headers(session["access_token"]))
        assert response.status_code == 403


def test_manager_cannot_access_admin_users() -> None:
    with TestClient(app) as client:
        session = login(client, "smirnova@sunstay.example")
        response = client.get("/api/admin/users", headers=auth_headers(session["access_token"]))
        assert response.status_code == 403


def test_reports_and_pdf() -> None:
    with TestClient(app) as client:
        session = login(client, "smirnova@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get("/api/reports/occupancy", headers=headers)
        assert response.status_code == 200
        assert "series" in response.json()

        response = client.get("/api/manager/folios/1/pdf", headers=headers)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/pdf")
        assert response.content.startswith(b"%PDF")


def test_sql_injection_login_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "' OR 1=1 --", "password": "anything"},
        )
        assert response.status_code in (401, 422)


def test_admin_login_and_settings() -> None:
    with TestClient(app) as client:
        session = login(client, "dba@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get("/api/admin/users", headers=headers)
        assert response.status_code == 200
        response = client.get("/api/admin/settings", headers=headers)
        assert response.status_code == 200


def test_admin_users_stats_reasons_and_masking() -> None:
    with TestClient(app) as client:
        session = login(client, "dba@sunstay.example")
        headers = auth_headers(session["access_token"])

        stats = client.get("/api/admin/users/stats", headers=headers)
        assert stats.status_code == 200
        payload = stats.json()
        assert payload["summary"]["total"] >= 5
        assert "online" in payload["summary"]

        reasons = client.get("/api/admin/users/block-reasons", headers=headers)
        assert reasons.status_code == 200
        assert len(reasons.json()) >= 4

        users = client.get("/api/admin/users", headers=headers, params={"page_size": 5})
        assert users.status_code == 200
        items = users.json()["items"]
        assert items
        assert "is_online" in items[0]
        assert "*" in (items[0]["phone"] or "")


def test_audit_filters_and_login_events() -> None:
    with TestClient(app) as client:
        session = login(client, "dba@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get(
            "/api/admin/audit",
            headers=headers,
            params={"event_type": "LOGIN_SECURITY", "page_size": 5},
        )
        assert response.status_code == 200
        assert "items" in response.json()


def test_contacts_are_masked_in_manager_api() -> None:
    with TestClient(app) as client:
        session = login(client, "smirnova@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get("/api/manager/bookings/2", headers=headers)
        assert response.status_code == 200
        booking = response.json()["booking"]
        assert "*" in booking["document_number"]
        assert "*" in booking["guest_phone"]
        assert "@" in booking["guest_email"]


def test_backup_status_and_schedule() -> None:
    with TestClient(app) as client:
        session = login(client, "dba@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get("/api/admin/backups", headers=headers)
        assert response.status_code == 200
        payload = response.json()
        assert "settings" in payload
        assert payload["settings"]["backup.schedule_time"]


def test_public_calendar_reviews_currencies() -> None:
    with TestClient(app) as client:
        calendar = client.get("/api/public/calendar", params={"month": "2026-12"})
        assert calendar.status_code == 200
        assert "days" in calendar.json()
        assert len(calendar.json()["days"]) > 0

        reviews = client.get("/api/public/reviews")
        assert reviews.status_code == 200
        assert isinstance(reviews.json(), list)

        currencies = client.get("/api/public/currencies")
        assert currencies.status_code == 200
        assert currencies.json()["rates"]["RUB"] == 1


def test_admin_reviews_list_and_moderation() -> None:
    with TestClient(app) as client:
        session = login(client, "dba@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get("/api/admin/reviews", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_manager_waitlist_list() -> None:
    with TestClient(app) as client:
        session = login(client, "smirnova@sunstay.example")
        headers = auth_headers(session["access_token"])
        response = client.get("/api/manager/waitlist", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
