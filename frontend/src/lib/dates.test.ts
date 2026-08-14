import { describe, expect, it } from "vitest"

import { formatDate, pageCount } from "./dates"

describe("pageCount", () => {
  it("returns at least one page", () => {
    expect(pageCount(0, 20)).toBe(1)
  })

  it("rounds up by page size", () => {
    expect(pageCount(21, 20)).toBe(2)
  })
})

describe("formatDate", () => {
  it("returns an em dash for empty values", () => {
    expect(formatDate(null)).toBe("—")
    expect(formatDate(undefined)).toBe("—")
  })

  it("formats a valid ISO date", () => {
    expect(formatDate("2026-01-15")).toMatch(/2026/)
  })
})
