import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { http, HttpResponse } from "msw"
import { describe, expect, it } from "vitest"

import { ProjectTaskSection } from "./ProjectTaskSection"
import { projectFixture, taskFixture } from "@/test/fixtures"
import { renderWithProviders } from "@/test/render"
import { server } from "@/test/setup"

describe("ProjectTaskSection", () => {
  it("sends the debounced search term as a query param", async () => {
    const user = userEvent.setup()
    const requests: URL[] = []
    server.use(
      http.get("*/api/v1/projects/:projectId/tasks", ({ request }) => {
        requests.push(new URL(request.url))
        return HttpResponse.json({
          items: [taskFixture],
          total: 1,
          page: 1,
          page_size: 20,
        })
      }),
    )

    renderWithProviders(
      <ProjectTaskSection
        projectId={projectFixture.id}
        members={projectFixture.members}
      />,
    )

    await screen.findByText("Write copy")
    await user.type(screen.getByLabelText("Search tasks"), "copy")

    await waitFor(() => {
      expect(
        requests.some((url) => url.searchParams.get("search") === "copy"),
      ).toBe(true)
    })
  })
})
