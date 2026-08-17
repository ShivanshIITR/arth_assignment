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

The SPA is served by nginx on [http://localhost:8080](http://localhost:8080). Requests to `/api` (including the WebSocket at `/api/v1/ws/projects/{id}`) are proxied to the `backend` service, so the browser stays on one origin. Redis and the Arq worker start with the same command.

Backend-only Compose still lives in `backend/docker-compose.yml` if you only need Postgres and the API.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Vite dev server (port 5173) |
| `npm run build` | Typecheck and production build |
| `npm run lint` | Oxlint |
| `npm run typecheck` | TypeScript project build |
| `npm test` | Vitest unit and integration tests |
| `npm run test:e2e` | Playwright journeys (backend must be running, including Redis) |
| `npm run generate:types` | Regenerate `src/types/api.generated.ts` from `backend/docs/openapi.json` |

`src/types/api.generated.ts` is produced from `backend/docs/openapi.json`. Re-run `python scripts/export_openapi.py` in `backend/` then `npm run generate:types` whenever the API contract changes. Do not edit the generated file by hand.

Project pages show a membership-scoped activity feed and, for owners, an audit log. Task boards subscribe to live WebSocket updates. Task detail supports authenticated file attachments (upload progress, download, delete).

## Stack

- Vite + React + TypeScript
- Tailwind CSS + shadcn/ui
- TanStack Query, Zustand, Axios, React Hook Form, Zod
- dnd-kit for optional board drag-and-drop

## Trade-offs

- **Vite SPA instead of Next.js.** This is an authenticated client behind an API; SSR/App Router conventions add little here. Next.js (or a similar full-stack framework) is the usual production choice when you need SEO, SSR, or colocated BFF routes.
- **TanStack Query for server state instead of Redux Toolkit / hand-rolled `useEffect` fetching.** Caching, invalidation, pagination, and retries are the hard part; Query owns that. Redux (or another global store) remains common for complex client-side workflows, but once server data lives in Query there is almost nothing left for it to manage here.
- **Zustand for auth (in-memory access token) instead of React Context alone, and never `localStorage` for tokens.** The Axios interceptor must read/write the token outside the React tree; Zustand exposes that without reinventing a store. Production auth often adds a BFF or stricter session cookies only; refresh stays httpOnly on the API.
- **Axios instead of native `fetch`.** Interceptors make silent refresh (one in-flight `/auth/refresh`, then retry) straightforward. `fetch` can do the same with more boilerplate; either is fine in production if the refresh coordination is correct.
- **shadcn/ui + Tailwind instead of MUI / Mantine.** Components live in-repo and stay easy to restyle. Heavier component libraries are a common production pick when you want a large prebuilt catalog and accept their design system.
- **Native WebSocket client instead of Socket.IO.** The protocol is plain JSON invalidation signals (`task_changed` / `attachment_changed`), not rooms/ack/fallback transports. Socket.IO (or a managed realtime service) is the usual production choice for multi-instance fan-out, reconnect semantics, and broader client support.
- **Lightweight WS payload + `invalidateQueries` instead of pushing full task objects or replaying missed events.** Avoids a second serialization path that can drift from REST `TaskRead`. On reconnect, one full refetch is preferred over event replay; production realtime systems often keep sequence numbers / replay buffers when bandwidth and consistency requirements demand it.
- **Authenticated blob download instead of a plain `<a href>`.** The download endpoint needs a Bearer token; a direct link would not. Signed URLs (typical with S3) are the usual production alternative when the browser should download without custom client code.
- **Status change via `setQueryData` + refetch-on-error instead of full optimistic snapshot/rollback.** Completing a task can legitimately fail PBAC validation; simple invalidation is safer than hand-rolled rollback. Textbook optimistic updates (or a more formal optimistic layer) fit better when failures are rare and easy to reverse.
- **dnd-kit as additive board UX instead of making drag-and-drop load-bearing.** Status still works from a dropdown. `react-beautiful-dnd` is unmaintained; dnd-kit (or a design-system DnD) is the maintained production-leaning option.