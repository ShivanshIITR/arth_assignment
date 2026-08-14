import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { Route, Routes } from "react-router-dom"
import { describe, expect, it } from "vitest"

import { LoginPage } from "./LoginPage"
import { useAuthStore } from "./store"
import { renderWithProviders } from "@/test/render"

describe("LoginPage", () => {
  it("stores the session and redirects after a successful login", async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<p>Dashboard home</p>} />
      </Routes>,
      { route: "/login" },
    )

    await user.type(screen.getByLabelText("Email"), "owner@example.com")
    await user.type(screen.getByLabelText("Password"), "password12")
    await user.click(screen.getByRole("button", { name: "Sign in" }))

    await waitFor(() => {
      expect(screen.getByText("Dashboard home")).toBeInTheDocument()
    })
    expect(useAuthStore.getState().accessToken).toBe("access-token")
    expect(useAuthStore.getState().user?.email).toBe("owner@example.com")
  })

  it("shows field errors when the form is submitted empty", async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />, { route: "/login" })
    await user.click(screen.getByRole("button", { name: "Sign in" }))
    expect(await screen.findByText("Enter a valid email address")).toBeInTheDocument()
    expect(screen.getByText("Password is required")).toBeInTheDocument()
  })
})
