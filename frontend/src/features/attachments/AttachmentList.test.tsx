import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { delay, http, HttpResponse } from "msw"
import { describe, expect, it } from "vitest"

import { AttachmentList } from "./AttachmentList"
import {
  attachmentFixture,
  memberFixture,
  taskFixture,
  userFixture,
} from "@/test/fixtures"
import { renderWithProviders } from "@/test/render"
import { server } from "@/test/setup"

const file = new File(["hello world"], "notes.txt", { type: "text/plain" })

describe("AttachmentList", () => {
  it("uploads a file and lists it", async () => {
    const user = userEvent.setup()
    let items = [] as typeof attachmentFixture[]
    server.use(
      http.get("*/api/v1/tasks/:taskId/attachments", () =>
        HttpResponse.json({ items }),
      ),
      http.post("*/api/v1/tasks/:taskId/attachments", async () => {
        items = [{ ...attachmentFixture, original_filename: "notes.txt" }]
        return HttpResponse.json(items[0], { status: 201 })
      }),
    )

    renderWithProviders(
      <AttachmentList
        taskId={taskFixture.id}
        currentUserId={userFixture.id}
        isOwner
      />,
    )

    expect(await screen.findByText("No attachments yet")).toBeInTheDocument()
    await user.upload(screen.getByLabelText("Upload file"), file)
    expect(await screen.findByText("notes.txt")).toBeInTheDocument()
  })

  it("shows an upload error from the API envelope", async () => {
    const user = userEvent.setup()
    server.use(
      http.post("*/api/v1/tasks/:taskId/attachments", () =>
        HttpResponse.json(
          { error: { code: "PAYLOAD_TOO_LARGE", message: "File too large" } },
          { status: 413 },
        ),
      ),
    )

    renderWithProviders(
      <AttachmentList
        taskId={taskFixture.id}
        currentUserId={userFixture.id}
        isOwner
      />,
    )

    await screen.findByText("No attachments yet")
    await user.upload(screen.getByLabelText("Upload file"), file)
    expect(await screen.findByText("File too large")).toBeInTheDocument()
  })

  it("shows upload progress while the request is in flight", async () => {
    const user = userEvent.setup()
    server.use(
      http.post("*/api/v1/tasks/:taskId/attachments", async () => {
        await delay(80)
        return HttpResponse.json(attachmentFixture, { status: 201 })
      }),
    )

    renderWithProviders(
      <AttachmentList
        taskId={taskFixture.id}
        currentUserId={userFixture.id}
        isOwner
      />,
    )

    await screen.findByText("No attachments yet")
    await user.upload(screen.getByLabelText("Upload file"), file)
    expect(screen.getByRole("progressbar", { name: "Upload progress" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Uploading…" })).toBeDisabled()
    await waitFor(() => {
      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument()
    })
  })

  it("shows delete for the uploader or project owner only", async () => {
    server.use(
      http.get("*/api/v1/tasks/:taskId/attachments", () =>
        HttpResponse.json({ items: [attachmentFixture] }),
      ),
    )

    const { unmount } = renderWithProviders(
      <AttachmentList
        taskId={taskFixture.id}
        currentUserId={userFixture.id}
        isOwner
      />,
    )
    expect(await screen.findByText("spec.txt")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument()
    unmount()

    const { unmount: unmountUploader } = renderWithProviders(
      <AttachmentList
        taskId={taskFixture.id}
        currentUserId={memberFixture.id}
        isOwner={false}
      />,
    )
    expect(await screen.findByText("spec.txt")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument()
    unmountUploader()

    renderWithProviders(
      <AttachmentList
        taskId={taskFixture.id}
        currentUserId="33333333-3333-3333-3333-333333333333"
        isOwner={false}
      />,
    )
    expect(await screen.findByText("spec.txt")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument()
  })
})
