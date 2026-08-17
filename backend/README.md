# Project Management Platform API

FastAPI backend for a lightweight project management platform. It provides JWT authentication, project and task CRUD, search/filter/pagination, dashboard aggregates, an activity timeline, audit logging, file attachments, live WebSocket updates, Redis cache-aside for hot reads, and a centralized policy-based access control (PBAC) layer. Role-based access control is not used.

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
| Cache / jobs | Redis 7 + Arq | Cache-aside for dashboard/project detail; email jobs retry independently of the API process |

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
| POST | `/auth/logout-all` | Revoke the whole refresh-token family |
| GET | `/auth/me` | Current user |
| POST | `/projects` | Caller becomes owner and member |
| GET | `/projects` | Membership-scoped list |
| GET/PATCH/DELETE | `/projects/{id}` | View / owner update / owner delete |
| POST/DELETE | `/projects/{id}/members` | Owner adds by email / removes by user id |
| GET | `/projects/{id}/activity` | Membership-scoped activity timeline |
| GET | `/projects/{id}/audit-logs` | Owner-scoped project audit log |
| GET | `/users/me/audit-logs` | Caller's own auth/audit history |
| POST/GET | `/projects/{id}/tasks` | Create; list with `status`, `priority`, `search`, `page`, `page_size` |
| GET/PATCH/DELETE | `/tasks/{id}` | Detail / update / delete |
| POST/GET | `/tasks/{id}/attachments` | Multipart upload; list |
| GET | `/attachments/{id}/download` | Authorized file stream |
| DELETE | `/attachments/{id}` | Uploader or project owner |
| GET | `/dashboard/stats` | Aggregates across the caller's projects |
| WS | `/ws/projects/{id}` | First-message JWT auth; live task/attachment events |
| GET | `/health` | Liveness |

List responses:

```json
{ "items": [], "total": 0, "page": 1, "page_size": 20 }
```

Errors:

```json
{ "error": { "code": "FORBIDDEN", "message": "..." } }
```

Oversized uploads use the same envelope with `413` / `PAYLOAD_TOO_LARGE`.

## PBAC policies

Configured in `app/policies/policies.yaml`:

- `project:view` — member
- `project:update` / `project:delete` — owner
- `task:create` — member (resource is the **project**; the task does not exist yet)
- `task:update` — creator, assignee, **or** project owner
- `task:delete` — todo **and** project owner
- `task:complete` — has assignee **and** required fields
- `timeline:view` — member
- `attachment:view` / `attachment:create` — member
- `attachment:delete` — uploader **or** project owner

Audit-log visibility is query-scoped (project owner / self), not a new role. Adding a rule: write a predicate, register it, add a YAML entry. `authorize()` does not change.

## Setup

Requires Python 3.12+ and Docker (for Postgres).

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Start Postgres and Redis, migrate, run the API:

```bash
docker compose up db redis -d
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Email jobs need the worker as well (`arq app.jobs.worker.WorkerSettings`), or use the full Compose stack below. `EMAIL_BACKEND=console` logs messages instead of sending SMTP.

### Docker (full stack)

```bash
cp .env.example .env
docker compose up --build
```

The backend waits for Postgres, runs `alembic upgrade head`, then serves on port 8000. Redis, the API, and the Arq worker come up together. Attachments persist on the `uploads_data` volume.

### Tests

```bash
docker compose -f docker-compose.test.yml up -d --wait
pytest
```

CI runs lint (Ruff, Black), pytest against Postgres 16 and Redis 7, then `docker build`.

Regenerate the exported OpenAPI document (and then frontend types) after API changes:

```bash
PYTHONPATH=. python scripts/export_openapi.py
```

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
| `REDIS_URL` | Shared by cache-aside and Arq |
| `ARQ_MAX_TRIES` | Email job retries (default 3) |
| `EMAIL_BACKEND` | `console` (default) or `smtp` |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `MAIL_FROM` | Used when `EMAIL_BACKEND=smtp` |
| `UPLOAD_DIR` | Local attachment storage (Compose mounts `/app/uploads`) |
| `MAX_ATTACHMENT_SIZE_MB` | Default 10 |

Compose overrides `DATABASE_URL` and `REDIS_URL` so containers talk to the `db` and `redis` services even if `.env` points at localhost.

## Assumptions

- **Task completion “required information”** means title, assignee, priority, and due date are all set. Change `task_required_fields_complete` in `app/policies/predicates.py` if a reviewer wants a different definition.
- **Active project** means the project has at least one task whose status is not `completed`. Projects with no tasks are counted in `total_projects` but not in `active_projects`.
- The project owner is always inserted into `project_members` on create, so membership listings and `project:view` stay consistent. Ownership itself is `projects.owner_id`, not a role.
- Assignees must already be project members.
- A new task cannot be created with status `completed`.
- The project owner cannot be removed from the member list.
- Removing a member transfers `creator_id` on their tasks in that project to the project owner.

## Trade-offs

- **Offset pagination** (`page` / `page_size`) instead of keyset / cursor pagination. Cost grows with page depth, but this is a small-team tool (tens to low hundreds of tasks per project) and page numbers map cleanly to a UI. The logic lives in `utils/pagination.py` and `TaskRepository.list_filtered` so a later switch is contained.
- **`pg_trgm` GIN index** on `tasks.title` for `ILIKE '%term%'` rather than Postgres full-text search (or an external search engine like Elasticsearch / OpenSearch). Search is substring match, not ranked natural language.
- **Redis cache-aside, not a source of truth** (and not a write-through / distributed cache as the system of record). Dashboard stats and project detail are cached with short TTLs and event-driven invalidation. If Redis is down, reads fall back to Postgres.
- **Refresh-token families with reuse detection** instead of opaque long-lived sessions alone, or a dedicated auth service. A replayed refresh token revokes the family; a short grace window covers concurrent tabs. Production hardening beyond this would usually add device/session inventories and stricter absolute lifetimes.
- **Arq for email, not FastAPI `BackgroundTasks`.** SMTP can fail; jobs retry in a separate worker. Delivery is best-effort, not exactly-once. Celery (or a managed queue) would be the usual production choice for richer routing, monitoring, and multi-language workers; Arq was chosen because the stack is already async and Redis is already required for cache.
- **In-process WebSocket fan-out.** One API replica is enough for this Compose assignment; Redis Pub/Sub (or a managed realtime layer) would be the next step for multiple API processes.
- **Local filesystem attachments** behind a `StorageBackend` protocol, instead of S3 / MinIO. Magic-byte checks are hand-rolled instead of `python-magic`. Blocking `mkdir` / `open` / `read` / `write` / `unlink` run in a worker thread via `asyncio.to_thread` so they don't stall the event loop; `aiofiles` was skipped to avoid an extra dependency. The upload request still waits until the file is on disk. S3-compatible object storage is the usual production choice; the protocol keeps that a one-backend swap later.
- **Hand-rolled PBAC** instead of Casbin (or a hosted authorization service). Policies do not justify a DSL; the YAML + predicate registry is easier to review.
- **No generic `AbstractRepository`.** Queries such as `list_for_user` and `list_filtered` are domain-specific; a CRUD base would get in the way. A shared repository base is a common large-codebase pattern, but it would not earn its keep here.
- **Connection pool 5+5** for a single Compose replica. At multiple replicas, `replica_count × (pool_size + max_overflow)` must stay under Postgres `max_connections`; PgBouncer (or a managed pooler) is the next step, not included here.

## Database

Postgres 16. Notable schema choices:

- Native enums for task status and priority
- Composite PK on `project_members (project_id, user_id)` plus reverse index `(user_id, project_id)`
- Composite index `tasks (project_id, status, priority, created_at)`
- Unique hashed refresh tokens, stored with a family id for reuse detection
- Conditional delete `DELETE FROM tasks WHERE id = :id AND status = 'todo'` so a concurrent status change cannot silently delete an in-progress task
- `activity_logs` and `audit_logs` are append-only from the API (no update/delete endpoints)
- `attachments` store original filename and an opaque storage path; the file bytes live on disk / the Compose volume

Migrations live in `app/db/migrations/versions/`.
