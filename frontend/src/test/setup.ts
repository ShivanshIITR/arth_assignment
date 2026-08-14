import { setupServer } from "msw/node"
import { afterAll, afterEach, beforeAll } from "vitest"

import { useAuthStore } from "@/features/auth/store"
import { resetAuthRefreshState } from "@/lib/apiClient"
import { queryClient } from "@/lib/queryClient"

import { handlers } from "./handlers"

import "@testing-library/jest-dom/vitest"

export const server = setupServer(...handlers)

beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" })
})

afterEach(() => {
  server.resetHandlers()
  useAuthStore.getState().clear()
  queryClient.clear()
  resetAuthRefreshState()
})

afterAll(() => {
  server.close()
})
