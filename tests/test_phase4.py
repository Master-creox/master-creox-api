"""Phase 4 tests: built-in CreoXEngine (offline, deterministic), chat
endpoints, SSE streaming, conversation memory, usage enrichment, /models.

No network call, no third-party API, and no API key is ever used here —
the engine answers from its own knowledge base.
"""
import json
import os

os.environ["MASTER_CREOX_ADMIN_KEY"] = "test-admin"
os.environ["DATABASE_PATH"] = ":memory:"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.tables import UsageLog  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.creox_engine import CreoXEngine  # noqa: E402

client = TestClient(create_app())
MODEL = "creox"


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


def _chat_key(email):
    h = _user(email)
    return _key(h, ["chat"])


# --- Engine unit tests (offline, deterministic) ---

def test_engine_answers_phishing_question():
    result = CreoXEngine().complete(
        [{"role": "user", "content": "How do I spot a phishing email?"}], MODEL)
    assert "phishing" in result.reply.lower()
    assert result.model == MODEL


def test_engine_answers_ransomware_question():
    result = CreoXEngine().complete(
        [{"role": "user", "content": "What is ransomware and how do I stay safe?"}], MODEL)
    assert "ransomware" in result.reply.lower()


def test_engine_answers_ai_voice_scam_question():
    result = CreoXEngine().complete(
        [{"role": "user", "content": "Someone called with a cloned voice asking for money, what do I do?"}],
        MODEL)
    assert "voice" in result.reply.lower()


def test_engine_handles_greeting():
    result = CreoXEngine().complete([{"role": "user", "content": "Hello"}], MODEL)
    assert "hello" in result.reply.lower()


def test_engine_honest_fallback_for_unknown_topic():
    result = CreoXEngine().complete(
        [{"role": "user", "content": "What is the capital of France?"}], MODEL)
    assert "france" not in result.reply.lower()
    assert "cybersecurity" in result.reply.lower()
    assert "password-check" in result.reply


def test_engine_token_counts_are_word_counts():
    result = CreoXEngine().complete(
        [{"role": "user", "content": "one two three"}], MODEL)
    assert result.prompt_tokens == 3
    assert result.completion_tokens == len(result.reply.split())
    assert result.total_tokens == result.prompt_tokens + result.completion_tokens


def test_engine_scores_last_user_message():
    result = CreoXEngine().complete(
        [{"role": "user", "content": "Tell me about ransomware"},
         {"role": "assistant", "content": "Ransomware locks files."},
         {"role": "user", "content": "How do I spot a phishing email?"}], MODEL)
    assert "phishing" in result.reply.lower()


# --- Endpoint auth / validation (real engine, no monkeypatching) ---

def test_chat_requires_chat_scope():
    h = _user("p4-scope@example.com")
    _, tools_key = _key(h, ["tools"])
    r = client.post("/api/v1/chat/completions",
                    json={"model": MODEL, "messages": [{"role": "user", "content": "Hi"}]},
                    headers={"X-API-Key": tools_key})
    assert r.status_code == 401, r.text


def test_chat_requires_key():
    r = client.post("/api/v1/chat/completions",
                    json={"model": MODEL, "messages": [{"role": "user", "content": "Hi"}]})
    assert r.status_code == 401, r.text


def test_chat_unsupported_model():
    _, key = _chat_key("p4-model@example.com")
    r = client.post("/api/v1/chat/completions",
                    json={"model": "gpt-4", "messages": [{"role": "user", "content": "Hi"}]},
                    headers={"X-API-Key": key})
    assert r.status_code == 400, r.text
    assert r.json()["error"]["code"] == "unsupported_model"


# --- Happy paths (real engine) ---

def test_chat_happy_path():
    _, key = _chat_key("p4-happy@example.com")
    r = client.post("/api/v1/chat/completions",
                    json={"model": MODEL, "messages": [{"role": "user", "content": "What is phishing?"}]},
                    headers={"X-API-Key": key})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "phishing" in body["reply"].lower()
    assert body["model"] == MODEL
    assert body["usage"]["total_tokens"] == (body["usage"]["prompt_tokens"]
                                            + body["usage"]["completion_tokens"])
    assert body["session_id"]


def test_chat_creox_brain_alias():
    _, key = _chat_key("p4-alias@example.com")
    r = client.post("/api/v1/chat/completions",
                    json={"model": "creox-brain", "messages": [{"role": "user", "content": "What is phishing?"}]},
                    headers={"X-API-Key": key})
    assert r.status_code == 200, r.text
    assert r.json()["model"] == MODEL


def test_chat_streaming():
    _, key = _chat_key("p4-stream@example.com")
    kh = {"X-API-Key": key}
    payload = {"model": MODEL, "messages": [{"role": "user", "content": "What is ransomware?"}]}
    plain = client.post("/api/v1/chat/completions", json=payload, headers=kh)
    assert plain.status_code == 200, plain.text
    r = client.post("/api/v1/chat/completions?stream=true", json=payload, headers=kh)
    assert r.status_code == 200, r.text
    assert "text/event-stream" in r.headers["content-type"]
    assert "data: [DONE]" in r.text
    deltas = []
    for line in r.text.splitlines():
        if line.startswith("data: ") and line != "data: [DONE]":
            deltas.append(json.loads(line[6:])["delta"])
    assert "".join(deltas).strip() == plain.json()["reply"]


# --- Conversation memory ---

def test_session_round_trip():
    _, key = _chat_key("p4-session@example.com")
    kh = {"X-API-Key": key}
    s = client.post("/api/v1/chat/sessions", json={"title": "My chat"}, headers=kh)
    assert s.status_code == 201, s.text
    sid = s.json()["id"]
    assert s.json()["title"] == "My chat"
    for text in ("What is phishing?", "What is ransomware?"):
        r = client.post("/api/v1/chat/completions",
                        json={"model": MODEL, "session_id": sid,
                              "messages": [{"role": "user", "content": text}]},
                        headers=kh)
        assert r.status_code == 200, r.text
        assert r.json()["session_id"] == sid
    msgs = client.get(f"/api/v1/chat/sessions/{sid}/messages", headers=kh)
    assert msgs.status_code == 200, msgs.text
    got = msgs.json()["messages"]
    assert len(got) == 4
    assert [m["role"] for m in got] == ["user", "assistant", "user", "assistant"]
    assert got[0]["content"] == "What is phishing?"
    assert got[2]["content"] == "What is ransomware?"
    listing = client.get("/api/v1/chat/sessions", headers=kh)
    assert any(x["id"] == sid for x in listing.json()["sessions"])


def test_session_ownership():
    _, key_a = _chat_key("p4-owner-a@example.com")
    _, key_b = _chat_key("p4-owner-b@example.com")
    sid = client.post("/api/v1/chat/sessions", json={}, headers={"X-API-Key": key_a}).json()["id"]
    assert client.get(f"/api/v1/chat/sessions/{sid}/messages",
                      headers={"X-API-Key": key_b}).status_code == 404
    r = client.post("/api/v1/chat/completions",
                    json={"model": MODEL, "session_id": sid,
                          "messages": [{"role": "user", "content": "Hi"}]},
                    headers={"X-API-Key": key_b})
    assert r.status_code == 404, r.text


# --- Usage enrichment + /models status ---

def test_usage_enrichment():
    _, key = _chat_key("p4-usage@example.com")
    r = client.post("/api/v1/chat/completions",
                    json={"model": MODEL, "messages": [{"role": "user", "content": "What is phishing?"}]},
                    headers={"X-API-Key": key})
    assert r.status_code == 200, r.text
    with SessionLocal() as s:
        row = s.scalars(select(UsageLog).where(
            UsageLog.endpoint == "/api/v1/chat/completions"
        ).order_by(UsageLog.id.desc())).first()
    assert row is not None
    assert row.model == MODEL
    assert (row.tokens or 0) > 0


def test_models_returns_creox_active_without_key():
    _, key = _chat_key("p4-models@example.com")
    r = client.get("/api/v1/models", headers={"X-API-Key": key})
    assert r.status_code == 200, r.text
    entry = r.json()["models"][0]
    assert entry["id"] == MODEL
    assert entry["type"] == "local"
    assert entry["provider"] == "creox"
    assert entry["status"] == "active"
