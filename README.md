# Chancery

![CI](https://github.com/Valdemar262/fast-api/actions/workflows/ci.yml/badge.svg)
![coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)
![python](https://img.shields.io/badge/python-3.12-blue)

Resource booking and approval API, written from scratch in Python/FastAPI as a
port of an existing Laravel application. Built as a portfolio project: the goal
was not a one-to-one translation but a clean, tested, idiomatic Python service —
including fixing several design problems found in the original along the way.

## What it does

Clients register, create **statements** (requests for a resource), submit them
for review, and **book** resources for a time range. Administrators approve or
reject statements, manage resources and users, and download CSV reports.

- JWT authentication with separate access and refresh tokens
- Two roles (`client`, `admin`) enforced per route
- CRUD for resources, with Redis caching and invalidation
- Bookings with real time-range overlap detection
- Statements with a `draft → submitted → approved/rejected` state machine,
  implemented with the Strategy pattern, and a full status history
- Email notifications delivered by a Celery worker
- Four aggregate CSV reports
- 163 tests, 90% coverage, `ruff` + `mypy --strict` clean, all enforced in CI

## Tech stack

| | |
|---|---|
| Web | FastAPI (ASGI, async) |
| Database | PostgreSQL, SQLAlchemy 2.0 async, Alembic |
| Validation | Pydantic v2, pydantic-settings |
| Cache & broker | Redis |
| Background jobs | Celery |
| Auth | PyJWT, Argon2 (`pwdlib`) |
| Tests | pytest, pytest-asyncio, httpx |
| Tooling | uv, ruff, mypy, Docker Compose, GitHub Actions |

## Architecture

Four layers, with dependencies pointing in one direction only:

```
HTTP
 │
 ▼
api/            routers, dependencies, HTTP status codes
 │              (the only layer that knows about HTTP)
 ▼
services/       business rules, transaction boundaries
 │              (raise domain exceptions, never HTTPException)
 ▼
repositories/   data access — the only place that builds SQL
 │
 ▼
models/         SQLAlchemy ORM, database schema
```

Supporting modules:

```
src/app/
├── core/           config, security, mail, cache, logging
├── schemas/        Pydantic models — the API contract
├── notification/   email notifications (ABC + subclasses)
├── reports/        CSV report builders (ABC + subclasses)
├── tasks/          Celery tasks
├── cache/          cache key builders
└── cli.py          create-admin, seed
```

Two rules hold everywhere:

- **SQL lives only in `repositories/`.** Services ask for data, they do not
  build queries.
- **Services never raise `HTTPException`.** They raise domain errors from
  `exceptions.py`, and a single handler in `main.py` maps them to status codes.
  The same services can be called from the CLI or a Celery task unchanged.

## Design decisions

**JWT instead of an OAuth2 server.** The original uses Laravel Passport with
four database tables. Full OAuth2 exists to delegate access to third-party
applications; here there is one first-party client, so signed stateless tokens
are the right size for the problem.

**A `type` claim inside the token.** Access and refresh tokens are signed with
the same key and are otherwise indistinguishable — without the claim a refresh
token would work as a 30-day access token.

**A `role` column instead of RBAC tables.** The original pulls in
`spatie/laravel-permission` with three tables, but only ever uses two fixed
roles. An enum column matches actual usage.

**Repositories `flush()`, services `commit()`.** One business operation is one
transaction. Approving a statement updates the statement *and* writes a history
row; if the second write fails, the first is rolled back with it. If every
repository committed on its own, that guarantee would be gone.

**`lazy="raise"` on every relationship.** Touching a relationship that was not
explicitly loaded raises instead of silently issuing another query. N+1 becomes
a loud error during development rather than a slow endpoint in production.

**`Protocol` for transition strategies, `ABC` for notifications and reports.**
The strategies share no implementation, so a structural contract is enough;
notifications and reports do share code (`send()`, `render()`), which is what
an abstract base class is for.

**Cache invalidation by deletion, not update.** Writes delete the affected keys
and let the next reader repopulate them. Updating cached values in place is
harder to get right under concurrent writes.

**Redis errors are swallowed, Celery errors are not.** A cache is an
accelerator and must never become a single point of failure, so cache failures
are logged and ignored. A failing mail task must propagate, because that is how
Celery knows to retry it.

**No `asyncio.gather` in the reports.** It was considered for the independent
aggregations, but `AsyncSession` is not safe for concurrent use, and opening
extra sessions to save milliseconds is not a good trade here.

## Improvements over the original

Ported deliberately differently, with reasons:

| Original | Here |
|---|---|
| `createBooking` performed no conflict check at all; the "conflict" helper compared only the user/resource pair, ignoring time | Real interval overlap detection (`start < other.end AND end > other.start`), covered by all seven boundary cases |
| `approved_by` had `ON DELETE CASCADE` — deleting an admin deleted every statement they had approved | `ON DELETE SET NULL` |
| `allStatements()` returned the whole table | Pagination on every list endpoint, with `items` and `total` computed from the same filter |
| `showStatement` and `updateUser` did not check ownership — any id could be read or edited | Ownership checks on every single-object route (IDOR closed) |
| An empty collection raised `CollectionEmptyException` | An empty collection is a valid `200` with `items: []` |
| Approval looked the resource up by matching its name against the statement title | Approval uses the statement's own `resource_id` |
| No automated tests | 163 tests, 90% coverage, enforced in CI |

## Getting started

Requirements: Docker and Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Then apply migrations and seed development data:

```bash
docker compose exec api alembic upgrade head
```

```bash
docker compose exec api python -m app.cli seed --fresh
```

The seed creates `admin@example.com` and `client@example.com`, both with the
password `password123`, plus a few resources.

| | |
|---|---|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Mailpit (caught emails) | http://localhost:8025 |
| Health | `GET /health`, `GET /health/db` |

To authenticate in Swagger: call `POST /api/v1/auth/login`, copy
`tokens.access_token`, then press **Authorize** and paste it.

## CLI

```bash
docker compose exec api python -m app.cli seed --fresh
```

```bash
docker compose exec api python -m app.cli create-admin --name Admin --email admin@example.com --password password123
```

`create-admin` is idempotent: it promotes the user if the email already exists.
`--fresh` truncates every table and resets id sequences; it refuses to run
outside the `local` and `test` environments.

## Development

```bash
docker compose exec api pytest -v
```

```bash
docker compose exec api ruff check src tests --fix && docker compose exec api ruff format src tests
```

```bash
docker compose exec api mypy src tests
```

Dependencies are added on the host (`uv add <package>`), then the image is
rebuilt — the container is a build artifact, not a place to install things.

Tests use a separate database and roll back a transaction after each test, so
they neither pollute the development database nor depend on each other. The
message broker is never contacted: an autouse fixture records what would have
been queued.

## Migrations

```bash
docker compose exec api alembic revision --autogenerate -m "describe the change"
```

```bash
docker compose exec api alembic upgrade head
```

```bash
docker compose exec api alembic check
```

`alembic check` verifies that the models and the database schema agree.
Autogenerated migrations are always reviewed before being applied: Alembic
cannot detect renames (it emits drop + add, losing data) and does not generate
`ALTER TYPE ... ADD VALUE` for new enum members.

## Project history

[`PLAN.md`](PLAN.md) tracks the phases the project was built in, each mapped to
the part of the Laravel application it ports, along with the decisions taken at
each step.
