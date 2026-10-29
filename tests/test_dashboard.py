"""v0.6.0 dashboard: HTML page + key detail + line-by-line usage."""
import os

os.environ.setdefault("MASTER_CREOX_ADMIN_KEY", "test-admin-key")

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app

ADMIN = {"X-Admin-Key": "test-admin-key"}


@pytest.fixture(autouse=True)
def _admin_key():
    """Temporarily enable the admin key for this module only, then restore
    it — other test modules expect admin to be unconfigured."""
    original = settings.admin_key
    object.__setattr__(settings, "admin_key", "test-admin-key")
    yield
    object.__setattr__(settings, "admin_key", original)


def _client():
    return TestClient(create_app())


def test_dashboard_page_returns_html():
    r = _client().get("/api/v1/dashboard")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Generate Key" in r.text
    assert "All Keys" in r.text


def test_admin_panels_hidden_by_default():
    # Admin sections exist in the HTML but are gated behind ?admin=1 in JS,
    # and the public view shows only a public note — no admin data is
    # rendered server-side into the page at all.
    html = _client().get("/api/v1/dashboard").text
    assert 'class="panel admin-only"><h2>Admin Access' in html
    assert 'admin") === "1"' in html
    assert "public view" in html
    assert "MASTER_CREOX_ADMIN_KEY" not in html.replace(
        "Paste MASTER_CREOX_ADMIN_KEY here", "")


def test_friend_working_window_present_without_admin():
    html = _client().get("/api/v1/dashboard").text
    assert "Your API Key" in html
    assert "Chat — CreoX" in html
    assert "Show my usage" in html
    # Working window calls user-scoped endpoints only — never /keys or /admin.
    assert "/chat/completions" in html and "/tools/password-check" in html
    assert "/usage/breakdown" in html


def test_key_detail_and_usage_flow():
    c = _client()
    created = c.post("/api/v1/keys", json={"name": "dash-test", "scopes": ["chat"]}, headers=ADMIN).json()
    assert created["key"].startswith("mcx_")
    kid = created["id"]
    detail = c.get(f"/api/v1/keys/{kid}", headers=ADMIN)
    assert detail.status_code == 200
    assert detail.json()["key"]["name"] == "dash-test"
    assert "recent" in detail.json() and "usage" in detail.json()
    usage = c.get(f"/api/v1/keys/{kid}/usage", headers=ADMIN)
    assert usage.status_code == 200
    recent = c.get("/api/v1/admin/usage/recent?limit=5", headers=ADMIN)
    assert recent.status_code == 200
    assert "recent" in recent.json()
    assert c.get("/api/v1/keys", headers={"X-Admin-Key": "wrong"}).status_code == 401
