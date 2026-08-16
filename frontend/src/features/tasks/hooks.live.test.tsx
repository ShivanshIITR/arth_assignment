import { beforeEach, describe, expect, it, vi } from "vitest"

import { useAuthStore } from "@/features/auth/store"
import { queryKeys } from "@/lib/queryKeys"
import {
  connectProjectSocket,
  type ProjectSocketHandlers,
} from "@/lib/websocketClient"
import { projectFixture } from "@/test/fixtures"
import { renderWithProviders } from "@/test/render"

import { useTaskLiveUpdates } from "./hooks"

vi.mock("@/lib/websocketClient", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/websocketClient")>()
  return {
    ...actual,
    connectProjectSocket: vi.fn(() => () => undefined),
  }
})

beforeEach(() => {
  vi.mocked(connectProjectSocket).mockClear()
})

function Probe({ projectId }: { projectId: string }) {
  useTaskLiveUpdates(projectId)
  return null
}

describe("useTaskLiveUpdates", () => {
  it("invalidates task and activity queries on task_changed", () => {
    useAuthStore.getState().setAccessToken("access-token")
    const { client } = renderWithProviders(
      <Probe projectId={projectFixture.id} />,
    )
    const invalidate = vi.spyOn(client, "invalidateQueries")
    const handlers = vi.mocked(connectProjectSocket).mock.calls.at(
      -1,
    )?.[2] as ProjectSocketHandlers

    handlers.onMessage({
      type: "task_changed",
      task_id: "t1",
      action: "updated",
    })

    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ["projects", projectFixture.id, "tasks"],
    })
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: queryKeys.projects.activity(projectFixture.id),
    })
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: queryKeys.tasks.detail("t1"),
    })
  })

  it("refetches collections on reconnect", () => {
    useAuthStore.getState().setAccessToken("access-token")
    const { client } = renderWithProviders(
      <Probe projectId={projectFixture.id} />,
    )
    const invalidate = vi.spyOn(client, "invalidateQueries")
    const handlers = vi.mocked(connectProjectSocket).mock.calls.at(
      -1,
    )?.[2] as ProjectSocketHandlers

    handlers.onReconnect?.()

    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ["projects", projectFixture.id, "tasks"],
    })
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: queryKeys.dashboard.stats,
    })
  })
})
