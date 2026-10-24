import os

os.environ["MASTER_CREOX_ADMIN_KEY"] = "test-admin"
os.environ["DATABASE_PATH"] = ":memory:"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402

client = TestClient(create_app())
ADMIN = {"X-Admin-Key": "test-admin"}


def _user(email):
    client.post("/api/v1/auth/register",
                json={"name": "Tester", "email": email, "password": "StrongPass1!"})
    r = client.post("/api/v1/auth/token", json={"email": email, "password": "StrongPass1!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_usage_tracking_and_stats():
    h = _user("usage@example.com")
    key = client.post("/api/v1/keys", json={"name": "k", "scopes": ["tools"]}, headers=h).json()["key"]
    kh = {"X-API-Key": key}
    client.post("/api/v1/tools/password-check", json={"password": "abc12345A!"}, headers=kh)
    client.post("/api/v1/tools/password-check", json={"password": "Better-Pass-99!"}, headers=kh)
    client.post("/api/v1/tools/phishing-check", json={"url": "https://example.com"}, headers=kh)
    stats = client.get("/api/v1/usage", headers=h)
    assert stats.status_code == 200, stats.text
    body = stats.json()
    assert body["total_requests"] >= 3
    assert body["by_endpoint"].get("/api/v1/tools/password-check") == 2
    assert body["by_endpoint"].get("/api/v1/tools/phishing-check") == 1


def test_admin_stats_and_users():
    _user("stats@example.com")
    stats = client.get("/api/v1/admin/stats", headers=ADMIN)
    assert stats.status_code == 200
    assert stats.json()["total_users"] >= 1 and "top_endpoints" in stats.json()
    users = client.get("/api/v1/admin/users", headers=ADMIN)
    assert any(u["email"] == "stats@example.com" for u in users.json()["users"])
    assert client.get("/api/v1/admin/stats").status_code in (401, 503)


def test_tampered_jwt_rejected():
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
    assert r.status_code == 401


def test_sql_injection_attempt_on_login_is_safe():
    r = client.post("/api/v1/auth/token",
                    json={"email": "' OR '1'='1", "password": "whatever"})
    assert r.status_code == 401  # not 200, not 500
