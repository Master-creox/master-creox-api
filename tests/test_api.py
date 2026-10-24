import os

os.environ["MASTER_CREOX_ADMIN_KEY"] = "test-admin"
os.environ["DATABASE_PATH"] = ":memory:"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402

client = TestClient(create_app())
ADMIN = {"X-Admin-Key": "test-admin"}


def _make_key(scopes=("tools",)):
    r = client.post("/api/v1/keys", json={"name": "test", "scopes": list(scopes)}, headers=ADMIN)
    assert r.status_code == 201, r.text
    return r.json()["key"]


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_tools_require_key():
    r = client.post("/api/v1/tools/password-check", json={"password": "x"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "missing_api_key"


def test_password_check_weak_and_strong():
    key = _make_key()
    h = {"X-API-Key": key}
    weak = client.post("/api/v1/tools/password-check", json={"password": "password123"}, headers=h)
    assert weak.status_code == 200 and weak.json()["score"] <= 1
    strong = client.post("/api/v1/tools/password-check",
                         json={"password": "Correct-Horse-Battery-42!"}, headers=h)
    assert strong.status_code == 200 and strong.json()["score"] >= 3


def test_phishing_check_flags_ip_url():
    key = _make_key()
    r = client.post("/api/v1/tools/phishing-check",
                    json={"url": "http://192.168.1.9/login-verify"}, headers={"X-API-Key": key})
    body = r.json()
    assert r.status_code == 200 and body["is_suspicious"] is True and body["risk_score"] >= 2


def test_revoked_key_stops_working():
    key = _make_key()
    kid = client.get("/api/v1/keys", headers=ADMIN).json()["keys"][-1]["id"]
    assert client.delete(f"/api/v1/keys/{kid}", headers=ADMIN).status_code == 200
    r = client.post("/api/v1/tools/password-check", json={"password": "whatever1A!"}, headers={"X-API-Key": key})
    assert r.status_code == 401


def test_admin_key_required_for_key_management():
    r = client.post("/api/v1/keys", json={"name": "nope"})
    assert r.status_code == 401
