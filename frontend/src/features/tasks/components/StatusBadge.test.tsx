import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { PriorityBadge, StatusBadge } from "./StatusBadge"

describe("StatusBadge", () => {
  it("renders a human-readable status label", () => {
    render(<StatusBadge status="in_progress" />)
    expect(screen.getByText("In progress")).toBeInTheDocument()
  })
})

describe("PriorityBadge", () => {
  it("renders a human-readable priority label", () => {
    render(<PriorityBadge priority="high" />)
    expect(screen.getByText("High")).toBeInTheDocument()
  })
})
