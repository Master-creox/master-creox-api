import os

os.environ["MASTER_CREOX_ADMIN_KEY"] = "test-admin"
os.environ["DATABASE_PATH"] = ":memory:"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402

client = TestClient(create_app())
ADMIN = {"X-Admin-Key": "test-admin"}


def _register(email="akash@example.com", password="StrongPass1!"):
    return client.post("/api/v1/auth/register",
                       json={"name": "Akash", "email": email, "password": password})


def _token(email="akash@example.com", password="StrongPass1!"):
    r = client.post("/api/v1/auth/token", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_register_login_me_flow():
    r = _register()
    assert r.status_code == 201 and r.json()["email"] == "akash@example.com"
    assert "password" not in r.text and "password_hash" not in r.text
    me = client.get("/api/v1/auth/me", headers=_token())
    assert me.status_code == 200 and me.json()["name"] == "Akash"


def test_login_wrong_password():
    _register("bob@example.com")
    r = client.post("/api/v1/auth/token", json={"email": "bob@example.com", "password": "WrongPass1!"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_credentials"


def test_register_duplicate_email():
    _register("dup@example.com")
    r = _register("dup@example.com")
    assert r.status_code == 409


def test_user_owns_keys():
    _register("owner@example.com")
    h = _token("owner@example.com")
    created = client.post("/api/v1/keys", json={"name": "mine", "scopes": ["tools"]}, headers=h)
    assert created.status_code == 201
    raw = created.json()["key"]
    use = client.post("/api/v1/tools/password-check", json={"password": "whatever1A!"},
                      headers={"X-API-Key": raw})
    assert use.status_code == 200
    mine = client.get("/api/v1/keys", headers=h).json()["keys"]
    assert len(mine) == 1 and mine[0]["name"] == "mine"
    kid = mine[0]["id"]
    assert client.delete(f"/api/v1/keys/{kid}", headers=h).status_code == 200
    again = client.post("/api/v1/tools/password-check", json={"password": "whatever1A!"},
                        headers={"X-API-Key": raw})
    assert again.status_code == 401


def test_users_cannot_see_each_others_keys():
    _register("u1@example.com")
    _register("u2@example.com")
    h1, h2 = _token("u1@example.com"), _token("u2@example.com")
    client.post("/api/v1/keys", json={"name": "u1key", "scopes": ["tools"]}, headers=h1)
    assert client.get("/api/v1/keys", headers=h2).json()["keys"] == []
    other_id = client.get("/api/v1/keys", headers=h1).json()["keys"][0]["id"]
    assert client.delete(f"/api/v1/keys/{other_id}", headers=h2).status_code == 404


def test_audit_logs_admin_only_and_recorded():
    _register("aud@example.com")
    _token("aud@example.com")
    logs = client.get("/api/v1/audit-logs", headers=ADMIN)
    assert logs.status_code == 200
    actions = [entry["action"] for entry in logs.json()["logs"]]
    assert "user.register" in actions and "auth.login" in actions
    assert client.get("/api/v1/audit-logs").status_code in (401, 503)


def test_rate_limit_kicks_in():
    limited = TestClient(create_app(rate_limit_per_minute=3))
    codes = [limited.get("/api/v1/models").status_code for _ in range(4)]
    assert codes[:3] == [401, 401, 401]
    assert codes[3] == 429
