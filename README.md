# Project Management Platform

Full-stack project management app: JWT auth, projects/tasks with PBAC (not RBAC), dashboard stats, activity timeline, audit logging, Redis cache-aside, background email jobs, live WebSocket updates, and file attachments.

## Quick start

```bash
docker compose up --build
```

| Surface | URL |
|---|---|
| Web UI | [http://localhost:8080](http://localhost:8080) |
| API docs | [http://localhost:8000/docs](http://localhost:8000/docs) |
| API health | [http://localhost:8000/health](http://localhost:8000/health) |

That one command brings up Postgres, Redis, the API, the Arq worker, and the nginx-served SPA. Copy `backend/.env.example` → `backend/.env` (and optionally `frontend/.env.example` → `frontend/.env`) before the first run if you need local overrides.

## Documentation

| Doc | Contents |
|---|---|
| [backend/README.md](backend/README.md) | Architecture, API overview, PBAC, env vars, migrations, tests, **trade-offs** |
| [frontend/README.md](frontend/README.md) | Setup, scripts, stack, OpenAPI types, **trade-offs** |
| [backend/docs/openapi.json](backend/docs/openapi.json) | Exported OpenAPI schema |
| [backend/docs/postman_collection.json](backend/docs/postman_collection.json) | Postman collection |

Design trade-offs and rejected alternatives (including stronger production options) live in the backend and frontend READMEs — not duplicated here.

## Layout

```text
.
├── backend/          # FastAPI + Postgres + Redis + Arq worker
├── frontend/         # Vite + React SPA
└── docker-compose.yml
```

Backend-only Compose (API + db + redis + worker) still lives in `backend/docker-compose.yml` if you do not need the UI container.
