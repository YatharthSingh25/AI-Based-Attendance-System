# Deployment Guide

This guide covers the security and database configuration required to deploy the
FastAPI backend and React frontend. It does not deploy anything itself.

## Prerequisites

- Python 3.11.9 (the project virtualenv is `backend/.venv`; Python 3.14 is incompatible)
- Node.js 18+ for the frontend build
- PostgreSQL 13+ for production (SQLite is supported for local tests only)
- HTTPS on both services

## Backend environment variables

Set these in the hosting dashboard (Render or equivalent). Do not commit a real
`.env`. Use `.env.example` as a placeholder template. For local runs, the backend
loads `backend/.env` (then a repo-root `.env`) without overriding variables that
are already set in the process environment.

| Variable | Required | Notes |
|---|---|---|
| `ENVIRONMENT` | Yes in production | `production` enables strict JWT and database validation. `development` is the local default. |
| `DATABASE_URL` | Yes in production | `postgresql://USER:PASSWORD@HOST:5432/DBNAME`. Production rejects a missing value, SQLite, and the local development default. |
| `JWT_SECRET` | Yes in production | Unique random value, at least 32 characters. Missing, known-default, or short values abort startup in production. |
| `JWT_ALGORITHM` | No | One of `HS256`, `HS384`, `HS512` (default `HS256`). |
| `JWT_EXPIRES_MINUTES` | No | Integer, 1-1440 (default `30`). |
| `CORS_ORIGINS` | Yes in production | Comma-separated exact browser origins, no trailing slash. Include the deployed frontend URL. |
| `PORT` | Platform-provided | Render sets it; the start command uses `$PORT`. |
| `PYTHON_VERSION` | Recommended | `3.11.9` (Python 3.14 is not compatible with the pinned dependencies). |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` / `ADMIN_NAME` | Only for seeding | Use with the admin seed command below, not on the web service. |

Generate a secret locally (never paste it into Git or logs):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Example production values:

```
ENVIRONMENT=production
DATABASE_URL=postgresql://attendance_user:REPLACE_ME@db-host:5432/attendance_ai
JWT_SECRET=REPLACE_WITH_GENERATED_SECRET
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=30
CORS_ORIGINS=https://your-frontend.example.com
```

If `ENVIRONMENT=production` and `JWT_SECRET` is absent, a known placeholder, or
shorter than 32 characters, the application raises a clear startup error and
does not serve requests. Error messages never contain the secret.

Production startup also validates the database configuration. It fails before
serving if `DATABASE_URL` is missing, uses SQLite, uses a non-PostgreSQL scheme,
or is still the local development default. `postgres://` is normalized to
`postgresql://`. URL-encode special characters in the username or password.

## Authentication behavior

- Public `POST /api/auth/register` may create `STUDENT` or `FACULTY` accounts.
  A requested `ADMIN`, `SUPERADMIN`, or any unknown role is replaced with
  `STUDENT` server-side.
- There is no public path to create `ADMIN` accounts.
- Bootstrap the first administrator with the environment-based seed command
  (from `backend/`):

```powershell
$env:ADMIN_EMAIL = "admin@example.com"
$env:ADMIN_PASSWORD = "REPLACE_WITH_STRONG_PASSWORD"
$env:ADMIN_NAME = "System Administrator"
.\.venv\Scripts\python.exe -m app.seed_admin
Remove-Item Env:\ADMIN_EMAIL, Env:\ADMIN_PASSWORD, Env:\ADMIN_NAME
```

The seed command:

- requires `ADMIN_EMAIL` and `ADMIN_PASSWORD` (minimum 12 characters);
- is idempotent for an existing admin;
- refuses to promote an existing non-admin account;
- never prints or logs the password.

Run it once against the production database (for example, a one-off job or
platform shell), then remove the admin variables from the web service.

## Database initialization

`backend/app/main.py` creates missing tables during application startup via
`create_db_and_tables()`, which:

- validates the production database configuration first;
- imports `app.models` so every model is registered on the metadata first;
- calls SQLAlchemy `create_all(..., checkfirst=True)`;
- only adds missing tables and never drops, truncates, or resets existing data.

The models use portable SQLAlchemy types (`Integer`, `String`, `Text`, `Float`,
`Boolean`, `Date`, `DateTime`) and are compatible with PostgreSQL. The only
SQLite-specific setting is the conditional `check_same_thread=False` argument in
`app/database.py`, which is not applied to PostgreSQL URLs. SQLite is for local
tests only and is rejected when `ENVIRONMENT=production`.

### Alembic status and migration risks

The working tree contains `backend/alembic.ini` and `backend/alembic/`, but they
are **not** the supported initialization path and are not committed as part of
this audit. Known risks before they can be used:

- `alembic/env.py` references `Base` without importing it, so it raises
  `NameError` as written.
- The initial revision does not fully match `app/models.py`: `audit_logs.id` is
  nullable, several foreign keys (`audit_logs.attendance_id`,
  `audit_logs.performed_by`, `ml_predictions.student_id`) are missing, and model
  indexes are absent.
- No Alembic migration has been run against PostgreSQL.

Supported path: let startup create missing tables with `create_all`. Do not run
`alembic upgrade head` in production unless the migration files are fixed and
verified separately.

## PostgreSQL verification

No PostgreSQL server or Docker runtime is available in this development
environment, so live PostgreSQL execution has **not** been performed here.
The live test below is **required before production use**; passing the offline
compilation checks is not proof that PostgreSQL accepts the schema.

Two checks are included:

1. Always-run offline compatibility tests compile every table with the
   PostgreSQL dialect and assert unique constraints/foreign keys:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest ..\tests\test_postgres_compat.py -v
```

2. Opt-in live test against a disposable PostgreSQL database. It creates a
   uniquely named schema, creates all tables there, verifies inserts,
   relationships, and the duplicate-attendance constraint, then drops the
   schema. Existing schemas/data are untouched.

```powershell
cd backend
$env:TEST_POSTGRES_URL = "postgresql://user:password@host:5432/disposable_db"
.\.venv\Scripts\python.exe -m pytest ..\tests\test_postgres_compat.py -v
Remove-Item Env:\TEST_POSTGRES_URL
```

The database user needs permission to create and drop a schema. If the
environment variable is unset, the live test is skipped (not silently passed).

`TEST_POSTGRES_URL` must point to a dedicated, disposable database. The live
test creates and drops only a randomly named schema inside that database; it
does not drop `public` or truncate existing tables. Do not reuse the production
database URL.

Separately, `tests/test_backend.py` accepts `TEST_DATABASE_URL`. SQLite uses a
local test file; PostgreSQL uses a unique schema and drops only that schema.
Leave it unset or point it only at a dedicated test database. Never set
`TEST_DATABASE_URL` to a production database.

## Backend deployment (Render)

This repository intentionally does not include an untested `render.yaml`
blueprint. Configure the service manually in the dashboard:

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Python version: `3.11.9` (set `PYTHON_VERSION=3.11.9`; Python 3.14 is not
  compatible with the pinned SQLAlchemy version)
- Environment variables: the table above. Use a generated `JWT_SECRET` of at
  least 32 characters and set `ENVIRONMENT=production`.

Attach a PostgreSQL instance and set `DATABASE_URL` to its connection string,
for example `postgresql://user:password@host:5432/dbname`. If the password
contains `@`, `:`, `/`, or other reserved characters, URL-encode it. Use the
provider's internal URL when the web service and database are in the same
region. The application creates missing tables on startup; do not pre-create
them with a conflicting schema.

## Frontend deployment

```powershell
cd frontend
npm.cmd ci
npm.cmd run lint
npm.cmd run build
```

Deploy `frontend/dist`. Set `VITE_API_BASE_URL` to the backend HTTPS origin
(for example `https://attendance-api.example.com`, no trailing slash) at build
time; Vite embeds it, so rebuild after changing it. Required frontend variables
are documented in `frontend/.env.example`:

| Variable | Notes |
|---|---|
| `VITE_API_BASE_URL` | Backend origin, e.g. `https://attendance-api.example.com` |
| `VITE_APP_NAME` | Display name |
| `VITE_ENVIRONMENT` | `production` |

After the frontend URL is known, add that exact origin to `CORS_ORIGINS` on the
backend. Local defaults allow `http://localhost:5173`, `http://127.0.0.1:5173`,
`http://localhost:3000`, and `http://127.0.0.1:3000`.

## Verification checklist

```powershell
cd backend
.\.venv\Scripts\python.exe -c "from app.main import app; print('Backend import successful'); print('Routes:', len(app.routes))"
.\.venv\Scripts\python.exe -m pytest ..\tests -v
cd ..\frontend
npm.cmd run lint
npm.cmd run build
```

Then verify against a running instance:

1. `GET /health` returns 200.
2. `POST /api/auth/register` with `"role": "ADMIN"` returns a `STUDENT` user.
3. Login with that account returns a bearer token.
4. `GET /api/students` with that `STUDENT` token returns 403.
5. Register a `FACULTY` account, log in, and confirm `GET /api/students` returns 200.
6. `POST /api/settings/thresholds` with the `FACULTY` token returns 403.
7. Login with a wrong password returns 401.
8. Production startup without a valid `JWT_SECRET` fails with a clear error.
9. Production startup without a PostgreSQL `DATABASE_URL` (or with SQLite/the
   local default) fails with a clear error.
10. The live PostgreSQL test has been run successfully against the target
    PostgreSQL version before go-live.

## Authorization policy

All routes below require a valid JWT. Authentication failures return 401; an
authenticated user whose role is not allowed returns 403. The checks are
enforced in the backend dependency, not only in the frontend.

| Routes | Allowed roles |
|---|---|
| `GET/POST/PUT/DELETE /api/students`, `POST /api/students/{id}/enroll-face` | `FACULTY`, `ADMIN` |
| `POST /api/attendance/sessions`, `GET /api/attendance/sessions`, `GET /api/attendance/{session_id}` | `FACULTY`, `ADMIN` |
| `POST /api/attendance/photo`, `POST /api/attendance/live/frame`, `POST /api/attendance/{id}/review` | `FACULTY`, `ADMIN` |
| `GET /api/analytics/overview`, `GET /api/analytics/student/{id}`, `POST /api/reports/export` | `FACULTY`, `ADMIN` |
| `GET /api/ml/predictions` | `FACULTY`, `ADMIN` |
| `GET /api/settings/*` | `FACULTY`, `ADMIN` |
| `POST /api/ml/train`, `POST /api/settings/*` | `ADMIN` |

Public routes remain `/health`, `POST /api/auth/login`, and
`POST /api/auth/register`. Public registration still creates only `STUDENT` or
`FACULTY`; `ADMIN` is provisioned only by `python -m app.seed_admin`.

The `STUDENT` role is authenticated but has no access to the current protected
staff/admin endpoints. This API has no student-facing record endpoints, so
there is no student ownership path to enforce; direct requests by a student to
student, attendance, analytics, or settings IDs return 403 before any lookup.
The frontend route guards are convenience only and are not the authorization
boundary.

## Known limitations

- Face detection/recognition and live attendance remain placeholders; no real
  biometric model is implemented or claimed.
- ML training is not implemented: `POST /api/ml/train` returns HTTP 501 with
  `status: "not_implemented"` and never reports a trained model.
- The `STUDENT` role has no student-facing endpoints in this build; staff routes
  return 403. Faculty also cannot modify settings or train ML models.
- Alembic migrations are present but unverified; startup `create_all` is the
  supported initialization path.
