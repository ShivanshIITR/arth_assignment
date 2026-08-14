# Project Management Platform API

FastAPI backend for a lightweight project management platform. It provides JWT authentication, project and task CRUD, search/filter/pagination, dashboard aggregates, and a centralized policy-based access control (PBAC) layer. Role-based access control is not used.

## Architecture

The app follows a layered layout so HTTP, business rules, authorization, and persistence stay separate:

```
Router  →  Service  →  Repository  →  PostgreSQL
              ↓
         PolicyEngine.authorize(user, action, resource)
```

| Layer | Responsibility |
|---|---|
| `app/api` | Parse/validate HTTP, call a service, return schemas |
| `app/services` | Business rules and transaction-sized units of work |
| `app/policies` | Yes/no authorization only (`policies.yaml` + predicates) |
| `app/repositories` | Domain-specific queries; never commit or roll back |
| `app/models` / `app/schemas` | ORM models vs per-operation Pydantic schemas |

Authorization for a single resource is `authorize(user, action, resource)` inside the service, next to the mutation it guards. List endpoints are scoped in SQL (`list_for_user`, `list_filtered`) instead of fetching rows and filtering in Python.

The parsed policy set is loaded once at startup onto `app.state.policy_engine`. A malformed `policies.yaml` fails boot.

## Technology choices

| Concern | Choice | Why |
|---|---|---|
| API | FastAPI | Async, Pydantic validation, OpenAPI/Swagger for free |
| ORM | SQLAlchemy 2.0 async + asyncpg | Explicit `select()`, matches FastAPI's event loop |
| Migrations | Alembic | Required deliverable; pairs with SQLAlchemy |
| Passwords | Argon2id (`argon2-cffi`) | Current OWASP recommendation |
| Tokens | PyJWT access token + opaque refresh cookie | Short-lived JWT; refresh tokens are hashed in the DB |
| Policies | YAML + predicate registry | Configurable PBAC without Casbin |
| Logging | structlog | JSON logs with a request id |
| Tests | pytest + httpx against real Postgres | Constraints/enums/indexes are actually exercised |

## API overview

Base URL: `/api/v1`

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Exported spec: [`docs/openapi.json`](docs/openapi.json)

Postman: [`docs/postman_collection.json`](docs/postman_collection.json)

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/register` | Create user |
| POST | `/auth/login` | Access token in body; refresh token as httpOnly cookie |
| POST | `/auth/refresh` | Rotate both tokens |
| POST | `/auth/logout` | Revoke refresh token, clear cookie |
| GET | `/auth/me` | Current user |
| POST | `/projects` | Caller becomes owner and member |
| GET | `/projects` | Membership-scoped list |
| GET/PATCH/DELETE | `/projects/{id}` | View / owner update / owner delete |
| POST/DELETE | `/projects/{id}/members` | Owner adds by email / removes by user id |
| POST/GET | `/projects/{id}/tasks` | Create; list with `status`, `priority`, `search`, `page`, `page_size` |
| GET/PATCH/DELETE | `/tasks/{id}` | Detail / update / delete |
| GET | `/dashboard/stats` | Aggregates across the caller's projects |
| GET | `/health` | Liveness |

List responses:

```json
{ "items": [], "total": 0, "page": 1, "page_size": 20 }
```

Errors:

```json
{ "error": { "code": "FORBIDDEN", "message": "..." } }
```

## PBAC policies

Configured in `app/policies/policies.yaml`:

- `project:view` — member
- `project:update` / `project:delete` — owner
- `task:create` — member (resource is the **project**; the task does not exist yet)
- `task:update` — creator, assignee, **or** project owner
- `task:delete` — todo **and** project owner
- `task:complete` — has assignee **and** required fields

Adding a rule: write a predicate, register it, add a YAML entry. `authorize()` does not change.

## Setup

Requires Python 3.12+ and Docker (for Postgres).

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Start Postgres, migrate, run the API:

```bash
docker compose up db -d
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker (full stack)

```bash
cp .env.example .env
docker compose up --build
```

The backend waits for Postgres, runs `alembic upgrade head`, then serves on port 8000.

### Tests

```bash
docker compose -f docker-compose.test.yml up -d --wait
pytest
```

CI runs lint (Ruff, Black), pytest against Postgres 16, then `docker build`.

## Environment variables

See `.env.example`. Important ones:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Async SQLAlchemy URL (`postgresql+asyncpg://...`) |
| `DATABASE_URL_SYNC` | Alembic URL (`postgresql+psycopg://...`) |
| `TEST_DATABASE_URL` | Pytest database |
| `JWT_SECRET_KEY` | Access-token signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Default 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Default 7 |
| `CORS_ORIGINS` | JSON list of allowed origins (credentials enabled) |
| `COOKIE_SECURE` | Set `true` behind HTTPS |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` | Defaults 5 / 5 |

Compose overrides `DATABASE_URL` so the app container talks to the `db` service even if `.env` points at localhost.

## Assumptions

- **Task completion “required information”** means title, assignee, priority, and due date are all set. Change `task_required_fields_complete` in `app/policies/predicates.py` if a reviewer wants a different definition.
- **Active project** means the project has at least one task whose status is not `completed`. Projects with no tasks are counted in `total_projects` but not in `active_projects`.
- The project owner is always inserted into `project_members` on create, so membership listings and `project:view` stay consistent. Ownership itself is `projects.owner_id`, not a role.
- Assignees must already be project members.
- A new task cannot be created with status `completed`.
- The project owner cannot be removed from the member list.
- Removing a member transfers `creator_id` on their tasks in that project to the project owner.

## Trade-offs

- **Offset pagination** (`page` / `page_size`) instead of keyset. Cost grows with page depth, but this is a small-team tool (tens to low hundreds of tasks per project) and page numbers map cleanly to a UI. The logic lives in `utils/pagination.py` and `TaskRepository.list_filtered` so a later switch is contained.
- **`pg_trgm` GIN index** on `tasks.title` for `ILIKE '%term%'` rather than Postgres full-text search. Search is substring match, not ranked natural language.
- **No Redis.** Caching authorization results or project payloads would leak data across users or go stale after membership changes. Dashboard counts would be the only safe candidate (short TTL, key includes user id).
- **Refresh rotation without token-family reuse detection.** Logout revokes the current refresh token; a stolen cookie that is rotated is invalidated. Full family revocation on replay is a later hardening step.
- **Hand-rolled PBAC** instead of Casbin. Six policies do not justify a DSL; the YAML + predicate registry is easier to review.
- **No generic `AbstractRepository`.** Queries such as `list_for_user` and `list_filtered` are domain-specific; a CRUD base would get in the way.
- **Connection pool 5+5** for a single Compose replica. At multiple replicas, `replica_count × (pool_size + max_overflow)` must stay under Postgres `max_connections`; PgBouncer is the next step, not included here.

## Database

Postgres 16. Notable schema choices:

- Native enums for task status and priority
- Composite PK on `project_members (project_id, user_id)` plus reverse index `(user_id, project_id)`
- Composite index `tasks (project_id, status, priority, created_at)`
- Unique hashed refresh tokens
- Conditional delete `DELETE FROM tasks WHERE id = :id AND status = 'todo'` so a concurrent status change cannot silently delete an in-progress task

Migrations live in `app/db/migrations/versions/`.
