import { http, HttpResponse } from "msw"

import {
  dashboardFixture,
  projectFixture,
  taskFixture,
  tokenFixture,
  userFixture,
} from "./fixtures"

const api = (path: string) => `*${path}`

export const handlers = [
  http.post(api("/api/v1/auth/register"), async ({ request }) => {
    const body = (await request.json()) as { email: string; full_name: string }
    return HttpResponse.json(
      { ...userFixture, email: body.email, full_name: body.full_name },
      { status: 201 },
    )
  }),
  http.post(api("/api/v1/auth/login"), () => HttpResponse.json(tokenFixture)),
  http.post(api("/api/v1/auth/refresh"), () => HttpResponse.json(tokenFixture)),
  http.post(api("/api/v1/auth/logout"), () => new HttpResponse(null, { status: 204 })),
  http.get(api("/api/v1/auth/me"), () => HttpResponse.json(userFixture)),
  http.get(api("/api/v1/projects"), () =>
    HttpResponse.json({
      items: [projectFixture],
      total: 1,
      page: 1,
      page_size: 12,
    }),
  ),
  http.get(api("/api/v1/projects/:projectId"), () =>
    HttpResponse.json(projectFixture),
  ),
  http.get(api("/api/v1/projects/:projectId/tasks"), () =>
    HttpResponse.json({
      items: [taskFixture],
      total: 1,
      page: 1,
      page_size: 20,
    }),
  ),
  http.get(api("/api/v1/dashboard/stats"), () =>
    HttpResponse.json(dashboardFixture),
  ),
]
