import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { StatCard } from "./StatCard"

describe("StatCard", () => {
  it("renders the label, value, and optional hint", () => {
    render(<StatCard label="Total tasks" value={12} hint="Across your projects" />)
    expect(screen.getByText("Total tasks")).toBeInTheDocument()
    expect(screen.getByText("12")).toBeInTheDocument()
    expect(screen.getByText("Across your projects")).toBeInTheDocument()
  })
})
