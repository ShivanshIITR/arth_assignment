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

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Vite dev server (port 5173) |
| `npm run build` | Typecheck and production build |
| `npm run lint` | Oxlint |
| `npm run generate:types` | Regenerate `src/types/api.generated.ts` from a live backend |

`src/types/api.generated.ts` is produced from the backend OpenAPI schema. Re-run `generate:types` whenever the API contract changes. Do not edit that file by hand.

## Stack

- Vite + React + TypeScript
- Tailwind CSS + shadcn/ui
- TanStack Query, Zustand, Axios, React Hook Form, Zod (added in later commits)
