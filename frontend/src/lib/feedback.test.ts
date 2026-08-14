import { toast } from "sonner"
import { describe, expect, it, vi } from "vitest"

import axios from "axios"

import { handleMutationError } from "./feedback"
import { queryClient } from "./queryClient"

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe("handleMutationError", () => {
  it("toasts the envelope message and invalidates on 403", async () => {
    const invalidate = vi.spyOn(queryClient, "invalidateQueries")
    const error = new axios.AxiosError(
      "Request failed",
      "ERR_BAD_REQUEST",
      undefined,
      undefined,
      {
        status: 403,
        statusText: "Forbidden",
        headers: {},
        config: { headers: new axios.AxiosHeaders() },
        data: {
          error: {
            code: "FORBIDDEN",
            message: "Only the project owner may delete a project",
          },
        },
      },
    )

    handleMutationError(error, {
      invalidateQueryKey: ["projects", "id"],
    })

    expect(toast.error).toHaveBeenCalledWith(
      "Only the project owner may delete a project",
    )
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ["projects", "id"],
    })
  })
})
