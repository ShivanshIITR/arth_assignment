import { screen } from "@testing-library/react"
import { http, HttpResponse } from "msw"
import { describe, expect, it } from "vitest"

import { formatActivitySentence } from "@/features/activity/format"
import { ActivityFeed } from "@/features/projects/components/ActivityFeed"
import { projectFixture, userFixture } from "@/test/fixtures"
import { renderWithProviders } from "@/test/render"
import { server } from "@/test/setup"
import type { ActivityLog } from "@/types/activity"

const baseEntry: ActivityLog = {
  id: "1",
  project_id: projectFixture.id,
  actor_id: userFixture.id,
  actor: userFixture,
  event_type: "TASK_CREATED",
  task_id: "t1",
  metadata: null,
  created_at: "2026-01-03T00:00:00Z",
}

describe("formatActivitySentence", () => {
  it("renders a sentence for each event type", () => {
    expect(formatActivitySentence({ ...baseEntry, event_type: "PROJECT_CREATED" })).toBe(
      "Owner User created the project",
    )
    expect(
      formatActivitySentence({
        ...baseEntry,
        event_type: "TASK_STATUS_CHANGED",
        metadata: { old_status: "todo", new_status: "completed" },
      }),
    ).toBe("Owner User changed a task from Todo to Completed")
    expect(
      formatActivitySentence({
        ...baseEntry,
        actor: null,
        actor_id: null,
        event_type: "TASK_REASSIGNED",
        metadata: { task_count: 2 },
      }),
    ).toBe("2 tasks reassigned to the project owner")
  })
})

describe("ActivityFeed", () => {
  it("renders activity sentences from the API", async () => {
    renderWithProviders(<ActivityFeed projectId={projectFixture.id} />)
    expect(await screen.findByText("Owner User created the project")).toBeInTheDocument()
  })

  it("shows an empty state when there is no activity", async () => {
    server.use(
      http.get("*/api/v1/projects/:projectId/activity", () =>
        HttpResponse.json({ items: [], total: 0, page: 1, page_size: 20 }),
      ),
    )
    renderWithProviders(<ActivityFeed projectId={projectFixture.id} />)
    expect(await screen.findByText("No activity yet")).toBeInTheDocument()
  })

  it("shows load more when another page exists", async () => {
    server.use(
      http.get("*/api/v1/projects/:projectId/activity", ({ request }) => {
        const url = new URL(request.url)
        const page = Number(url.searchParams.get("page") ?? "1")
        return HttpResponse.json({
          items: [
            {
              ...baseEntry,
              id: String(page),
              event_type: page === 1 ? "PROJECT_CREATED" : "TASK_CREATED",
            },
          ],
          total: 2,
          page,
          page_size: 1,
        })
      }),
    )
    renderWithProviders(<ActivityFeed projectId={projectFixture.id} />)
    expect(await screen.findByRole("button", { name: "Load more" })).toBeInTheDocument()
  })
})
