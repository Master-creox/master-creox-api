"""Phase 5 tests: key rotation, /developer/me, /usage/breakdown,
render.yaml + DEPLOY.md presence."""
import os
from pathlib import Path

os.environ["MASTER_CREOX_ADMIN_KEY"] = "test-admin"
os.environ["DATABASE_PATH"] = ":memory:"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import create_app  # noqa: E402

client = TestClient(create_app())
MODEL = "creox"
ROOT = Path(__file__).resolve().parents[1]


def _user(email):
    client.post("/api/v1/auth/register",
                json={"name": "Tester", "email": email, "password": "StrongPass1!"})
    r = client.post("/api/v1/auth/token", json={"email": email, "password": "StrongPass1!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _key(headers, scopes):
    r = client.post("/api/v1/keys", json={"name": "k", "scopes": scopes}, headers=headers)
    assert r.status_code == 201, r.text
    body = r.json()
    return body["id"], body["key"]


def test_key_rotation_works():
    h = _user("p5-rotate@example.com")
    kid, old_key = _key(h, ["chat"])
    r = client.post("/api/v1/developer/keys/rotate", json={"key_id": kid},
                    headers={"X-API-Key": old_key})
    assert r.status_code == 201, r.text
    new_key = r.json()["key"]
    assert new_key and new_key != old_key
    assert client.get("/api/v1/developer/me",
                      headers={"X-API-Key": old_key}).status_code == 401
    me = client.get("/api/v1/developer/me", headers={"X-API-Key": new_key})
    assert me.status_code == 200, me.text
    assert me.json()["key_name"] == "k"


def test_rotate_others_key_returns_404():
    h_a = _user("p5-owner-a@example.com")
    kid_a, _ = _key(h_a, ["chat"])
    h_b = _user("p5-owner-b@example.com")
    _, key_b = _key(h_b, ["chat"])
    r = client.post("/api/v1/developer/keys/rotate", json={"key_id": kid_a},
                    headers={"X-API-Key": key_b})
    assert r.status_code == 404, r.text


def test_developer_me_returns_keys_and_usage():
    h = _user("p5-me@example.com")
    kid, key = _key(h, ["tools"])
    kh = {"X-API-Key": key}
    client.post("/api/v1/tools/password-check", json={"password": "abc12345A!"}, headers=kh)
    me = client.get("/api/v1/developer/me", headers=kh)
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["key_id"] == kid
    assert any(k["id"] == kid for k in body["keys"])
    assert body["usage"]["total_requests"] >= 1


def test_usage_breakdown_shows_endpoint_and_model():
    h = _user("p5-breakdown@example.com")
    _, key = _key(h, ["chat"])
    kh = {"X-API-Key": key}
    r = client.post("/api/v1/chat/completions",
                    json={"model": MODEL, "messages": [{"role": "user", "content": "What is phishing?"}]},
                    headers=kh)
    assert r.status_code == 200, r.text
    bd = client.get("/api/v1/usage/breakdown", headers=kh)
    assert bd.status_code == 200, bd.text
    body = bd.json()
    assert body["by_endpoint"].get("/api/v1/chat/completions", 0) >= 1
    assert body["by_model"].get(MODEL, 0) >= 1
    assert body["total_tokens"] >= 6


def test_render_and_deploy_docs_exist():
    render = (ROOT / "render.yaml").read_text()
    assert "uvicorn" in render
    assert "master-creox-api" in render
    deploy = (ROOT / "DEPLOY.md").read_text()
    assert "Render" in deploy
    # The deploy guide must state the chat engine needs no provider key.
    assert "No AI provider key" in deploy
