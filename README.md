# Hourtime

A self-hosted time tracker: projects, a server-side timer, and an editable list
of everything you have tracked.

The timer lives on the backend, not in the browser tab. Reload the page, open a
different browser, come back tomorrow — the running entry is still there, and it
still counts from the moment it actually started.

## What is in the box

- **Accounts** — email and password, Argon2id hashes, opaque session tokens that
  can be revoked on the spot. Registration is behind a switch, because the
  instance is meant to face the open internet.
- **Projects** — a name and a colour, either from the preset palette or picked
  freely. Archive one to keep its history without it cluttering the picker.
- **Timer** — one running entry at a time, with an adjustable start time.
- **Entries** — a flat list where the comment, project, start and end of every
  entry can be edited or deleted.
- **Localisation** — every string goes through `vue-i18n`; English is the only
  language shipped so far.

## Stack

| Layer    | Choice                                                        |
| -------- | ------------------------------------------------------------- |
| Backend  | FastAPI, SQLAlchemy 2 (async, psycopg 3), Alembic, Pydantic v2 |
| Storage  | PostgreSQL 18, Redis 8 for the session cache                   |
| Frontend | Vue 3, TypeScript, Pinia, Vue Router, vue-i18n, Vite           |
| Tooling  | uv, ruff, ty, pytest                                           |

## Running it locally

Prerequisites: [uv](https://docs.astral.sh/uv/), Node 20+, Docker.

```bash
cp .env.example .env          # adjust if the defaults clash with something
docker compose up -d          # postgres + redis
```

Backend:

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python -m hourtime          # http://127.0.0.1:8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev                        # http://127.0.0.1:5173
```

The dev server proxies `/api` to the backend, so both run on one origin and CORS
only matters once they are deployed apart.

Open the app, create your account — then set `HOURTIME_ALLOW_REGISTRATION=false`
and restart the API so nobody else can.

> On Windows the API is started through `python -m hourtime` rather than the
> `uvicorn` CLI: uvicorn forces a ProactorEventLoop there, and psycopg's async
> driver cannot run on one.

## Checks

```bash
cd backend
uv run pytest                 # unit tests on fakes + API tests against Postgres
uv run ruff check .
uv run ty check

cd ../frontend
npm run typecheck
npm run build
```

The API tests create and migrate a throwaway `hourtime_test` database, so a
running Postgres is required; override its location with
`HOURTIME_TEST_DATABASE_URL`.

## How the backend is laid out

Dependencies point inwards: `domain` ← `interfaces` ← `use_cases` ←
`infrastructure` / `presentation`.

```
backend/src/hourtime/
  domain/          entities and errors — the rules, and nothing else
  interfaces/      the abstractions use cases are written against
  use_cases/       one class per scenario; no SQLAlchemy, no FastAPI, no Redis
  infrastructure/  Postgres, Redis, Argon2, the system clock
  presentation/    HTTP: routers, schemas, error mapping, composition root
```

Two consequences worth knowing:

- **Caching is invisible to the business logic.** `CachedSessionRepository` and
  `CachedUserRepository` wrap the SQL ones behind the plain repository
  interfaces, so an authenticated request resolves its bearer token entirely
  from Redis without a single use case knowing Redis exists. Only these two are
  cached: they are what *every* request reads, whereas projects and entries are
  read once per user action and would buy little for the invalidation they cost.
  A revoked session drops out of the cache immediately — `/auth/logout` takes
  effect on the next request, not when a TTL runs out. Rows edited straight in
  Postgres, on the other hand, stay stale until `HOURTIME_CACHE_TTL_SECONDS`
  elapses.
- **The database enforces the rules too.** A partial unique index on
  `time_entries (user_id) WHERE stopped_at IS NULL` is what actually guarantees
  one running timer per user; the use case only makes the hand-off graceful.
  Allowing parallel timers later is a matter of dropping that index.

## Sessions

Login hands out two opaque random tokens; the database stores only their
SHA-256 digests. Access tokens last 30 minutes, refresh tokens 30 days, and both
halves are replaced on every refresh. Using an already-rotated refresh token is
treated as a leak: every session of that user is revoked. Rows whose refresh
token expired more than `HOURTIME_SESSION_RETENTION_DAYS` ago are swept by a
background task.

The frontend therefore serialises refreshes — two concurrent ones would look
exactly like that leak.

## Configuration

Everything is read from `HOURTIME_*` environment variables; see
[`.env.example`](.env.example) for the full list with defaults. The ones worth
setting deliberately before exposing the instance:

| Variable                        | Why                                            |
| ------------------------------- | ---------------------------------------------- |
| `HOURTIME_ALLOW_REGISTRATION`   | Leave `false` once your account exists         |
| `HOURTIME_CORS_ORIGINS`         | The origin the frontend is actually served from |
| `HOURTIME_PASSWORD_MIN_LENGTH`  | Defaults to 10                                  |
| `HOURTIME_SESSION_RETENTION_DAYS` | How long dead sessions stay auditable         |

## Deploying

Build the frontend (`npm run build`) and serve `frontend/dist` as static files;
run the API behind a reverse proxy that terminates TLS and forwards `/api` to
uvicorn. Tokens travel in the `Authorization` header, so HTTPS is not optional —
without it, every session token is readable on the wire.
