import { http, HttpResponse, delay } from "msw"
import { describe, expect, it } from "vitest"

import { getCurrentUser } from "@/features/auth/api"
import { useAuthStore } from "@/features/auth/store"
import { userFixture } from "@/test/fixtures"
import { server } from "@/test/setup"

describe("silent refresh interceptor", () => {
  it("shares one refresh call across concurrent 401s", async () => {
    let refreshCalls = 0
    server.use(
      http.get("*/api/v1/auth/me", ({ request }) => {
        const auth = request.headers.get("authorization")
        if (auth !== "Bearer fresh-token") {
          return HttpResponse.json(
            { error: { code: "UNAUTHORIZED", message: "expired" } },
            { status: 401 },
          )
        }
        return HttpResponse.json(userFixture)
      }),
      http.post("*/api/v1/auth/refresh", async () => {
        refreshCalls += 1
        await delay(40)
        return HttpResponse.json({
          access_token: "fresh-token",
          token_type: "bearer",
          expires_in: 900,
        })
      }),
    )

    useAuthStore.getState().setAccessToken("expired-token")
    const users = await Promise.all([
      getCurrentUser(),
      getCurrentUser(),
      getCurrentUser(),
    ])

    expect(refreshCalls).toBe(1)
    expect(users).toHaveLength(3)
    expect(useAuthStore.getState().accessToken).toBe("fresh-token")
  })
})
