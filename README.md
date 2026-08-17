# Chancery

Resource booking API — a from-scratch Python/FastAPI port of an existing Laravel
application, built as a portfolio project to practice and demonstrate clean
backend architecture in Python.

## Status

Early stage: infrastructure and project skeleton are ready, domain logic is not
implemented yet.

- [x] Project layout (src-layout, layered architecture: repositories/services/api)
- [x] Docker infra: FastAPI + PostgreSQL + Redis
- [ ] Configuration & async DB session layer
- [ ] Domain models & Alembic migrations
- [ ] Auth (OAuth2 / JWT)
- [ ] Core domain: Resources, Bookings, Statements
- [ ] Background jobs (Celery)
- [ ] Tests

## Tech stack

- **FastAPI** — async web framework
- **SQLAlchemy 2.0 (async)** + **asyncpg** — ORM / database access
- **Alembic** — migrations
- **Pydantic v2 / pydantic-settings** — validation & config
- **PostgreSQL**, **Redis** — storage / cache / broker
- **uv** — dependency & environment management
- **pytest**, **ruff**, **mypy** — tests, linting, static typing
- **Docker / Docker Compose** — local infrastructure

## Project structure

```
src/app/
├── core/          # settings, logging, security
├── db/            # engine, session, declarative base
├── models/        # SQLAlchemy ORM models
├── schemas/       # Pydantic DTOs
├── repositories/  # data access layer
├── services/      # business logic
└── api/v1/        # routers, endpoints
```

## Getting started

Requirements: Docker, Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

API: http://localhost:8000
Health check: `GET /health`

## Swagger

```angular2html
http://localhost:8000/docs
```

## Environment variables

See `.env.example`.

## Command after start application

#### Create admin, user and 3 base resource in system
```bash
python -m app.cli seed --fresh
```

#### Create admin user in system
```bash
python -m app.cli create-admin
```