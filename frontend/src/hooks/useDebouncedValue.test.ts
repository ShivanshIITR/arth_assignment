import { act, renderHook } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { useDebouncedValue } from "./useDebouncedValue"

describe("useDebouncedValue", () => {
  it("updates after the delay and ignores stale values", () => {
    vi.useFakeTimers()
    const { result, rerender } = renderHook(
      ({ value }) => useDebouncedValue(value, 300),
      { initialProps: { value: "a" } },
    )

    expect(result.current).toBe("a")
    rerender({ value: "ab" })
    rerender({ value: "abc" })
    act(() => {
      vi.advanceTimersByTime(299)
    })
    expect(result.current).toBe("a")
    act(() => {
      vi.advanceTimersByTime(1)
    })
    expect(result.current).toBe("abc")
    vi.useRealTimers()
  })
})
