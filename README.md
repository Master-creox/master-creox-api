# Master CreoX API Platform

> One secure, scalable API platform powering **Jarvis**, **BabyCoach** and future CreoX projects.
> Built by [Master-creox](https://github.com/Master-creox) · License: **Apache-2.0** · Status: **Phase 5 — Developer Platform (complete)**

## What works today

### Phase 1 — Core API Foundation
- ⚡ FastAPI with versioned routes (`/api/v1`), global error format, request IDs, Swagger docs at `/docs`
- 🔑 API key system — keys shown once, only **SHA-256 hashes** stored, scopes enforced per endpoint
- 🛠️ Tool endpoints from CreoX's own ai-cyber-account-lab: `POST /tools/password-check`, `POST /tools/phishing-check`
- 🩺 `GET /health`, `GET /models` (model-adapter registry)

### Phase 2 — Identity & Security
- 👤 **User accounts** — `POST /auth/register`, Argon2 password hashing (passwords never stored in plain text)
- 🎫 **JWT login** — `POST /auth/token` issues a Bearer token; `GET /auth/me` returns your profile
- 🔐 **User-owned API keys** — logged-in users create/list/revoke **their own** keys; the bootstrap admin key still works
- 🚦 **Rate limiting** — per key/IP fixed window (default 100 req/min, `RATE_LIMIT_PER_MINUTE`); `429` + `Retry-After`
- 📜 **Audit log** — register/login/key events recorded; `GET /audit-logs` (admin only)

### Phase 3 — Database & Usage
- 🗄️ **SQLAlchemy 2.0 data layer** — SQLite for dev, PostgreSQL via `DATABASE_URL` (docker-compose ships Postgres 16); **Alembic migrations** in `migrations/`
- 📊 **Usage tracking** — every API call logged (endpoint, status, latency); `GET /usage` shows your totals, per-endpoint and per-day stats
- 🛠️ **Admin controls** — `GET /admin/users`, `GET /admin/stats` (platform totals + top endpoints), admin key only
- 🧪 **Security tests** — tampered-JWT rejection, SQL-injection login attempt, rate-limit and ownership suites (17 tests)

### Phase 4 — AI API Engine
- 💬 **Chat completions** — `POST /chat/completions` (scope `chat`) via the built-in **CreoX engine** (model `creox`, short alias `creox-brain` also accepted); other models return `400 unsupported_model`
- 📡 **SSE streaming** — `POST /chat/completions?stream=true` streams the reply word-by-word as `data: {"delta": "..."}` lines plus `data: [DONE]`
- 🧠 **Conversation memory** — `POST /chat/sessions`, `GET /chat/sessions`, `GET /chat/sessions/{id}/messages`; a session is readable only by its own key/user (others get 404)
- 📊 **Usage enrichment** — chat calls record `model` + `tokens` on the usage row; `GET /models` reports the built-in `creox` engine as always `active`
- 🔑 **No key needed** — the CreoX engine is built into the API, fully offline and deterministic; it answers cybersecurity-awareness questions from its own knowledge base and falls back honestly outside it

### Phase 5 — Developer Platform
- 🙋 **Self-service dashboard API** — `GET /developer/me` (your keys + usage summary) with any valid key, no scope required
- 🔄 **Key rotation** — `POST /developer/keys/rotate` revokes the old key and issues a replacement with the same name/scopes (shown once); rotating someone else's key returns 404
- 📈 **Usage breakdown** — `GET /usage/breakdown` shows per-endpoint, per-model and per-day totals for your key/user
- 🚀 **Deploy** — free-tier guide in [DEPLOY.md](DEPLOY.md): Render free web service + free Neon Postgres; `render.yaml` Blueprint included

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env   # set long random MASTER_CREOX_ADMIN_KEY and JWT_SECRET
uvicorn app.main:app --reload
# open http://127.0.0.1:8000/docs
```

Register → login → create your key:

```bash
curl -X POST localhost:8000/api/v1/auth/register -H 'Content-Type: application/json' \
  -d '{"name":"Akash","email":"you@example.com","password":"a-strong-password"}'
curl -X POST localhost:8000/api/v1/auth/token -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"a-strong-password"}'
# use the returned access_token as:  Authorization: Bearer <token>
```

## Roadmap (Master CreoX API Blueprint v1.0)

| Phase | Scope | Status |
|---|---|---|
| 1 | Core API foundation | ✅ |
| 2 | Identity & Security | ✅ this release |
| 3 | Database & Usage (PostgreSQL, migrations, usage stats API) | ✅ this release |
| 4 | AI API Engine (chat completions, built-in CreoX engine, streaming, memory) | ✅ this release |
| 5 | Developer Platform (self-service keys, usage breakdown, free deploy) | ✅ this release |

## Security rules

- Secrets live only in environment variables — never in code or git (`.env` is git-ignored).
- Passwords are hashed with **Argon2**; API keys are stored only as **SHA-256 hashes**.
- Passwords sent to `/tools/password-check` are assessed in memory and never stored or logged.
- The deployed API is key-protected; the public URL will be shared once it is deployed with production secrets.

## Tech stack

Python · FastAPI · Pydantic · PyJWT · Argon2 · SQLAlchemy 2.0 · Alembic · SQLite / PostgreSQL · Pytest · Docker
