# Project Management Platform — Frontend

React client for the project management API. Built with Vite, TypeScript, Tailwind CSS, and shadcn/ui.

## Setup

Requires Node 20+ and a running backend on port 8000 (see `../backend/README.md`).

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`, so auth cookies stay first-party.

## Docker

From the repository root:

```bash
docker compose up --build
```

The SPA is served by nginx on [http://localhost:8080](http://localhost:8080). Requests to `/api` are proxied to the `backend` service, so the browser stays on one origin.

Backend-only Compose still lives in `backend/docker-compose.yml` if you only need Postgres and the API.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Vite dev server (port 5173) |
| `npm run build` | Typecheck and production build |
| `npm run lint` | Oxlint |
| `npm test` | Vitest unit and integration tests |
| `npm run test:e2e` | Playwright journeys (backend must be running) |
| `npm run generate:types` | Regenerate `src/types/api.generated.ts` from a live backend |

`src/types/api.generated.ts` is produced from the backend OpenAPI schema. Re-run `generate:types` whenever the API contract changes. Do not edit that file by hand.

## Stack

- Vite + React + TypeScript
- Tailwind CSS + shadcn/ui
- TanStack Query, Zustand, Axios, React Hook Form, Zod
- dnd-kit for optional board drag-and-drop
