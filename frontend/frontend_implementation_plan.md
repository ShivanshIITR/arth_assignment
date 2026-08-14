# Frontend Implementation Plan — Project Management Platform Client

**Stack:** React.js (Vite + TypeScript) · TanStack Query · Tailwind CSS + shadcn/ui
**Architecture:** Feature-based, container/presentational split, server-state vs UI-state separation

---

## 1. Guiding Principles

| Principle | How it's applied here |
|---|---|
| **SRP** | Presentational components only render props; container components/hooks own data-fetching and logic. A `TaskCard` doesn't know how to fetch tasks; a `useTasks()` hook does. |
| **OCP** | Generic components (`DataTable`, `FilterBar`, `StatusBadge`) are extended via props/composition (slots, render props) — never modified per new feature. |
| **DIP** | Components never call `axios` or `fetch` directly. They depend on hooks (`useProjects`, `useCreateTask`) which depend on an abstracted `apiClient` — swapping the HTTP layer or mocking it for tests touches one file. |
| **Composition over inheritance** | UI built from small composable primitives (shadcn/ui pattern) rather than component subclassing. |
| **Single source of truth for server data** | TanStack Query cache is the only place server data lives — no duplicating project/task state into local `useState`, which is how UIs go stale. |

---

## 2. Tech Stack & Justification

| Concern | Choice | Why |
|---|---|---|
| Build tool | **Vite** | Fast dev server/HMR, minimal config, standard for modern React SPAs (CRA is deprecated). |
| Language | **TypeScript** | Type-safe API contracts matching backend Pydantic schemas; catches integration bugs at compile time. |
| Server state | **TanStack Query** | Purpose-built for exactly this problem (caching, background refetch, invalidation, pagination, optimistic updates) — writing this by hand in `useEffect` is what causes the "loading/error state everywhere" mess the assignment explicitly wants avoided. |
| Client/UI state | **Zustand** | Kept after reconsideration: the axios interceptor needs to read and mutate the token from *outside* the React tree (`useAuthStore.getState()`/`setState()`) to attach and refresh it, which plain Context can't do without hand-rolling the same imperative-access pattern. At one store (auth) plus a couple of ephemeral UI flags, Zustand costs a few KB and zero boilerplate — less code than reimplementing that access pattern manually. |
| Forms | **React Hook Form** | Uncontrolled-input performance (no re-render per keystroke), first-class TS support. |
| Validation | **Zod** | Schema-based validation shareable in shape with backend Pydantic schemas; integrates directly with RHF via `zodResolver`. |
| Routing | **React Router v6** | Standard for React SPAs; supports nested routes + loaders needed for `ProtectedRoute`. |
| HTTP client | **Axios** | Interceptor support is essential for the silent-refresh flow (attach access token, catch 401 → refresh → retry original request) — the native `fetch` requires hand-rolling this. |
| UI components | **Tailwind CSS + shadcn/ui** | shadcn ships accessible, unstyled-by-default Radix primitives copied into the repo (not an opaque npm dependency) — full control, easy to explain in review, no design-system fighting. |
| Search debouncing | **Custom `useDebouncedValue` hook (no library)** | Debouncing one search input is ~10 lines of `useEffect`/`setTimeout`; pulling in `use-debounce` or `lodash.debounce` for that is an unjustified dependency. |
| API types | **openapi-typescript (dev-time codegen)** | FastAPI already emits a full OpenAPI schema for free; one CLI command turns it into `types/api.generated.ts`, removing hand-maintained interfaces that silently drift from backend Pydantic schemas — real drift protection for near-zero setup cost. |
| Drag-and-drop (**bonus, built last**) | **dnd-kit** | Actively maintained, accessible (keyboard support), replaces the now-unmaintained `react-beautiful-dnd`. The required behavior (status change) ships first via a plain dropdown — dnd-kit is additive, not load-bearing, and is only started once all required CRUD/filter/search/pagination/validation/UI-state work is done. |
| Toasts/feedback | **sonner** | Lightweight, shadcn-recommended, covers "clear user feedback" requirement. |
| Unit/component tests | **Vitest + React Testing Library** | Vitest shares Vite's config/transform (no separate Jest config needed); RTL tests behavior, not implementation. |
| API mocking for tests | **MSW (Mock Service Worker)** | Intercepts at the network level, so components/hooks are tested exactly as they run in production — no mocking `axios` internals. |
| E2E (**bonus, cut first if time is tight**) | **Playwright** | Cross-browser, reliable auto-waiting, runs against the real dockerized full stack. |

**Explicitly rejected:** Redux Toolkit (overkill — no complex cross-cutting client state exists once server state is delegated to TanStack Query), Next.js (assignment allows it but SSR/routing conventions add nothing here since this is a pure authenticated SPA behind an API), Mantine/MUI (heavier bundle, harder to restyle away from their default look, less transparent than shadcn's copy-in-repo model), `use-debounce`/`lodash.debounce` (one input, ~10 lines — see Search debouncing row), manual optimistic-update snapshot/rollback bookkeeping for task status (§5 — `invalidateQueries` on error gets the same correctness with far less code).

---

## 3. Project Structure

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx                        # router setup
│   ├── components/
│   │   └── ui/                        # shadcn primitives (button, input, dialog, etc.)
│   ├── features/
│   │   ├── auth/
│   │   │   ├── api.ts                 # login/register/refresh/logout calls
│   │   │   ├── hooks.ts               # useLogin, useRegister, useCurrentUser
│   │   │   ├── store.ts               # Zustand: access token, user
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── projects/
│   │   │   ├── api.ts
│   │   │   ├── hooks.ts               # useProjects, useProject, useCreateProject...
│   │   │   ├── ProjectListPage.tsx
│   │   │   ├── ProjectDetailsPage.tsx
│   │   │   └── components/            # ProjectCard, MemberList, AddMemberDialog
│   │   ├── tasks/
│   │   │   ├── api.ts
│   │   │   ├── hooks.ts               # useTasks (with filters), useTask, useUpdateTaskStatus...
│   │   │   ├── TaskDetailsPage.tsx
│   │   │   └── components/            # TaskCard, TaskBoard (dnd-kit), TaskFilterBar, StatusBadge
│   │   └── dashboard/
│   │       ├── hooks.ts               # useDashboardStats
│   │       ├── DashboardPage.tsx
│   │       └── components/            # StatCard
│   ├── lib/
│   │   ├── apiClient.ts               # axios instance + interceptors (refresh flow: single in-flight refresh + _retry guard — §4.1)
│   │   ├── queryClient.ts             # TanStack Query client config
│   │   └── utils.ts
│   ├── hooks/
│   │   └── useDebouncedValue.ts       # generic debounce hook, used by task search (§6)
│   ├── routes/
│   │   └── ProtectedRoute.tsx
│   ├── types/
│   │   ├── api.generated.ts           # generated via `npm run generate:types` — never hand-edited
│   │   ├── project.ts                 # thin UI-only aliases on top of the generated API types
│   │   ├── task.ts
│   │   └── user.ts
│   └── test/
│       ├── setup.ts                   # RTL + MSW setup
│       └── handlers.ts                # MSW request handlers
├── e2e/                                # bonus — see §8, §10
│   ├── auth.spec.ts
│   ├── project-lifecycle.spec.ts
│   └── task-workflow.spec.ts
├── Dockerfile
├── nginx.conf
├── .env.example
├── vite.config.ts
├── vitest.config.ts
├── playwright.config.ts
└── tailwind.config.ts
```

`package.json` includes a `generate:types` script (`openapi-typescript http://localhost:8000/openapi.json -o src/types/api.generated.ts`), run once against a locally running backend and re-run whenever the API contract changes. It's a manual/dev-time step, not part of the build or CI pipeline, since it needs a live backend to introspect.

---

## 4. Auth Flow (Matches Backend Hybrid JWT)

1. On login/register, backend returns the access token in the JSON body and sets the refresh token as an httpOnly cookie (browser handles this automatically — JS never touches it).
2. Access token is stored **only** in the Zustand `authStore` (in-memory) — lost on hard refresh, by design.
3. On app load, an `AuthProvider` silently calls `/auth/refresh` (cookie sent automatically) to re-establish a session without asking the user to log in again.
4. Axios request interceptor attaches `Authorization: Bearer <token>` from the store.
5. Axios response interceptor: on `401`, triggers the coordinated refresh flow in §4.1 and retries the original request once a new token is available.
6. `ProtectedRoute` wraps authenticated routes, checks the store, redirects unauthenticated users.
7. Logout calls `/auth/logout` (revokes refresh token + clears cookie server-side) and clears the store.

### 4.1 Refresh Concurrency & Retry Safety

Several requests can 401 at once — e.g. the dashboard fires 3–4 queries in parallel right after the access token expires. Without coordination each would independently call `/auth/refresh`, and since refresh tokens rotate (backend §7), only the first call would succeed while the rest received an already-revoked token and failed.

- A module-level `refreshPromise: Promise<string> | null` in `apiClient.ts` is the single source of truth for "a refresh is in flight." The first 401 sets it and calls `/auth/refresh`; every other request that 401s while it's set **awaits that same promise** instead of starting its own refresh call, then retries with whatever token the one real call returned.
- `refreshPromise` is cleared in a `finally` block once the call settles, so the next expiry starts a clean cycle.
- Each retried request is tagged (`config._retry = true`) before being re-sent. If a retried request 401s **again**, no second refresh is attempted — it's treated as a terminal auth failure: clear the auth store, drop `refreshPromise`, redirect to `/login`. This is what prevents an infinite refresh → 401 → refresh loop when the refresh token itself is invalid or expired.
- If `/auth/refresh` itself returns a non-2xx, every request awaiting `refreshPromise` fails together and follows the same terminal path — no retry storm, no partial-success confusion.

### 4.2 401 vs 403 Handling

These are distinct failure modes and are handled differently:

- **401 Unauthorized** — the access token is missing/expired/invalid. Fully absorbed by §4.1's refresh flow; the calling component never sees a 401 directly, it either gets a successfully retried response or an auth-failure redirect.
- **403 Forbidden** — the token is valid but the backend's PBAC layer denied the action (e.g. a non-owner tried to delete a project, or a membership was revoked after the page loaded). This is **not** a token problem, so no refresh is attempted. The interceptor passes it straight through; the calling mutation's `onError` shows a toast using the backend's error envelope message and invalidates the relevant query so the UI re-syncs to the user's actual current access — covering the case where a control was visible only because the page hadn't refetched yet.
- This split is also why hiding buttons in the UI (§6) is a UX nicety, not enforcement: the backend can always return 403 even when a control was shown, and the frontend's only real job is to handle that response gracefully, not to prevent it from being possible.

---

## 5. State Management Strategy

- **Server state (projects, tasks, dashboard stats, user profile):** TanStack Query exclusively. Query keys are structured hierarchically (`['projects']`, `['projects', id]`, `['projects', id, 'tasks', filters]`) so mutations can precisely invalidate the exact cache entries they affect — see §5.1 for the full map.
- **Status changes (dropdown — required; drag-and-drop — bonus):** kept deliberately simple rather than a full optimistic-update system with manual snapshot/rollback. The status field is updated via `setQueryData` for an instant visual move, and on error the handler just calls `invalidateQueries` to refetch the authoritative state — no hand-maintained "previous value" bookkeeping to get wrong. This is a scaled-down version of the textbook optimistic-update pattern on purpose: task completion is subject to real backend validation (must have an assignee + all required fields — backend §5.4), so a rejected update is a real, expected case, and simple refetch-on-error is a better trade here than more code that has to get rollback exactly right. Task edits made through the full edit form are **not** optimistic — a form submission already has a natural loading affordance via `mutate` + per-button `isPending`.
- **Client/UI state:** Zustand for auth (kept — see §2 for the reconsidered justification); local `useState` for ephemeral things (dialog open/closed, form draft) — no global store pollution.

### 5.1 Mutation → Cache Invalidation Map

| Mutation | Invalidates / updates |
|---|---|
| Create project | `['projects']` |
| Update project | `['projects', id]`, and `['projects']` if the list view shows name/description |
| Delete project | `['projects']`; `removeQueries` for `['projects', id]` and `['projects', id, 'tasks', *]` |
| Add / remove member | `['projects', id]` (member list lives on the project-detail query) |
| Create task | `['projects', id, 'tasks', *]` (prefix match — all filter variants), `['dashboard', 'stats']` |
| Update task (fields) | `['projects', id, 'tasks', *]`, `['tasks', taskId]` |
| Update task status | same as above, **plus** `['dashboard', 'stats']` — a status change moves a task between the Completed/Pending counts |
| Delete task | `['projects', id, 'tasks', *]`, `['dashboard', 'stats']`; `removeQueries` for `['tasks', taskId]` |

`['projects', id, 'tasks', filters]` is always invalidated by **prefix match** (`queryClient.invalidateQueries({ queryKey: ['projects', id, 'tasks'] })`), not by reconstructing the exact filter object — TanStack Query invalidates every matching filter/page variant in one call.

---

## 6. Pages & Required Screens

| Page | Key elements |
|---|---|
| **Login / Register** | RHF + Zod validated forms, inline field errors, submit loading state, redirect on success |
| **Dashboard** | Stat cards (Total/Active Projects, Total/Completed/Pending Tasks) via `useDashboardStats`, skeleton loaders |
| **Project Listing** | Paginated grid/list of projects the user is a member of, create-project dialog, empty state for zero projects |
| **Project Details** | Project info (owner-only edit/delete controls, enforced by hiding + re-checked server-side), member list with add/remove (owner-only), task board or list scoped to the project |
| **Task Details** | Full task fields, edit form (RHF+Zod), status **dropdown** (required, built first) with drag-between-columns as an additive bonus (§2, §10), delete button hidden for non-owners as a UX nicety — actual authority is always server-side (§4.2) |
| Task list/board | Search input debounced via `useDebouncedValue` (300ms), with the debounced value included in the TanStack Query key so a fast keystroke never races or overwrites the latest search; status filter, priority filter, pagination controls |

**Important UX note:** control visibility here is UX only — see §4.2 for how the frontend actually handles a backend PBAC denial (403), which remains the sole source of authorization truth.

---

## 7. Validation, Loading, Empty & Error States

- Every form: Zod schema mirrors backend constraints (required fields, string lengths, enum values) for instant client-side feedback, but backend remains the source of truth.
- Every data-fetching component: three explicit render branches — `isLoading` (skeleton), `isError` (retry-capable error panel with the backend's error envelope message), and `data.length === 0` (empty state with a call-to-action, e.g., "No tasks yet — create one").
- Toasts (sonner) confirm mutations (task created, member removed, etc.) and surface API errors that aren't tied to a specific field.

---

## 8. Testing Plan

**Priority if the 2-day timeline gets tight:** required functionality (all CRUD, filtering, search, pagination, validation, PBAC-aware UI states) comes first, unconditionally. If time runs short, cut in this order: Playwright E2E first (it's a bonus, and the backend's own integration suite already exercises real PBAC enforcement end-to-end), then trim planned Integration cases, keeping Unit tests since they're already-written and cheap to keep. The non-negotiable minimum: the auth flow (§4) and at least one PBAC-denial integration test (a 403 correctly surfacing per §4.2) — highest value for the lowest cost.

| Layer | Tool | What's covered |
|---|---|---|
| **Unit** | Vitest + RTL | Pure components (`StatusBadge`, `StatCard`), hooks logic in isolation (e.g., filter-state reducer, `useDebouncedValue`), utils (date formatting, pagination math). |
| **Integration** | Vitest + RTL + MSW | Feature flows with the API mocked at the network layer: login form submits → store updates → redirect; refresh-concurrency behavior (§4.1) with multiple simultaneous 401s; task filter bar changes → correct query params sent → list re-renders; PBAC-driven UI (e.g., non-owner doesn't see delete button, and a mocked 403 shows the right toast per §4.2). |
| **E2E (bonus, cut first if time is tight)** | Playwright against `docker compose up` (real backend + real Postgres) | Full journeys: register → login → create project → add member → create task → assign → change status → verify dashboard stats update. Also verifies actual 403 enforcement, not just UI hiding. |

---

## 9. Docker

**Dockerfile** (multi-stage): `build` stage (`node:20-alpine`) runs `npm ci && npm run build`; `serve` stage (`nginx:alpine`) copies the static `dist/` output and a custom `nginx.conf` that serves the SPA with a fallback to `index.html` for client-side routing, and proxies `/api` to the backend service by name (`backend:8000`) inside the compose network — avoids CORS entirely in the containerized setup.

Joins the root `docker-compose.yml` as a `frontend` service depending on `backend`.

---

## 10. Suggested Commit Progression

1. Initialize project (Vite + TS + Tailwind + shadcn setup); generate API types from the backend's OpenAPI schema
2. Implement API client + auth store + silent-refresh interceptor, including the refresh-concurrency/`_retry` guard (§4.1)
3. Implement auth pages (login/register) + `ProtectedRoute`
4. Implement project listing + project details + member management
5. Implement task list/board with filter, debounced search, pagination
6. Implement task details + create/edit forms + status **dropdown** transition (required — no drag-and-drop yet)
7. Implement dashboard with stats
8. Add loading/empty/error states + toasts + 403-handling polish pass (§4.2)
9. Configure Docker + nginx
10. Add unit/integration tests for the required flows above (Vitest/RTL/MSW) — see §8 priority note
11. **Bonus, only once 1–10 are solid and time remains:** dnd-kit drag-and-drop, Playwright e2e suite
12. CI/CD (GitHub Actions: lint → typecheck → unit tests → build)
