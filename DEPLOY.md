# Deploying Master CreoX API (Phase 5)

Free-tier deployment: a **Render free web service** + a **free Postgres
database from Neon**. Nothing below costs money; the Render free service
sleeps after inactivity (first request after idle takes ~a minute).

## 1. Get a free Postgres database (Neon)

1. Create a free account at <https://neon.tech> and create a project.
2. Copy the connection string — it looks like
   `postgresql://user:password@host/dbname?sslmode=require`.
3. The app reads it as `DATABASE_URL`, but SQLAlchemy needs the
   `postgresql+psycopg` driver prefix, so use
   `postgresql+psycopg://user:password@host/dbname?sslmode=require`.

## 2. Deploy the API on Render

1. Push this repo to GitHub (the code is already deploy-ready).
2. In the [Render dashboard](https://dashboard.render.com), choose
   **New → Web Service**, connect the `master-creox-api` repo
   (or use this repo's `render.yaml` Blueprint).
3. Render detects the settings from `render.yaml`:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## 3. Set environment variables (Render dashboard only)

Set these in the service's **Environment** tab — never in code or git:

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | Your Neon URL with the `postgresql+psycopg://` prefix |
| `MASTER_CREOX_ADMIN_KEY` | A long random string (bootstrap admin key) |
| `JWT_SECRET` | A long random string (JWT signing secret) |
| `RATE_LIMIT_PER_MINUTE` | `100` |

No AI provider key exists: the chat engine is built into the API, so
`/chat/completions` works with no extra variable.

## 4. Verify

```bash
curl https://<your-service>.onrender.com/api/v1/health
# open https://<your-service>.onrender.com/docs for Swagger UI
```

## Security notes

- `.env` is git-ignored and is never committed; the only secrets are
  `MASTER_CREOX_ADMIN_KEY` and `JWT_SECRET`, set in the host's environment
  settings (Render dashboard), never in chat, code, or git history.
- If a key ever leaks, rotate it: `POST /developer/keys/rotate` with the
  old key, or revoke it via `DELETE /keys/{id}` — then update the value in
  the Render dashboard and redeploy.
- Run database migrations in production with Alembic
  (`alembic upgrade head`) before first use; local dev uses
  `Base.metadata.create_all` automatically.
