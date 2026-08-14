import axios from "axios"
import { describe, expect, it } from "vitest"

import { getApiErrorMessage, isForbiddenError } from "./apiError"

describe("getApiErrorMessage", () => {
  it("reads the backend error envelope", () => {
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
        data: { error: { code: "FORBIDDEN", message: "Only the owner may delete" } },
      },
    )
    expect(getApiErrorMessage(error)).toBe("Only the owner may delete")
    expect(isForbiddenError(error)).toBe(true)
  })

  it("falls back when the envelope is missing", () => {
    expect(getApiErrorMessage(new Error("boom"), "fallback")).toBe("boom")
  })
})
