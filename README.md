# Master CreoX API Platform

> One secure, scalable API platform powering **Jarvis**, **BabyCoach** and future CreoX projects.
> Built by [Master-creox](https://github.com/Master-creox) · License: **Apache-2.0** · Status: **Phase 2 — Identity & Security (complete)**

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
| 3 | Database & Usage (PostgreSQL, migrations, usage stats API) | next |
| 4 | AI API Engine (chat completions, model adapters, streaming) | planned |
| 5 | Developer Platform (dashboard, docs site, VPS + HTTPS) | planned |

## Security rules

- Secrets live only in environment variables — never in code or git (`.env` is git-ignored).
- Passwords are hashed with **Argon2**; API keys are stored only as **SHA-256 hashes**.
- Passwords sent to `/tools/password-check` are assessed in memory and never stored or logged.
- The deployed API is key-protected; the public URL will be shared once it is deployed with production secrets.

## Tech stack

Python · FastAPI · Pydantic · PyJWT · Argon2 · SQLite (Phase 1–2 → PostgreSQL Phase 3) · Pytest · Docker
