import { describe, expect, it, vi } from "vitest"

import { connectProjectSocket, type SocketMessage } from "@/lib/websocketClient"

type Listener = (event: Event) => void

function createFakeSocket() {
  const listeners = new Map<string, Set<Listener>>()
  const socket = {
    sent: [] as string[],
    readyState: 1,
    send(data: string) {
      this.sent.push(data)
    },
    close(code = 1000) {
      this.emit("close", new CloseEvent("close", { code }))
    },
    addEventListener(type: string, listener: EventListenerOrEventListenerObject) {
      const fn = listener as Listener
      const set = listeners.get(type) ?? new Set<Listener>()
      set.add(fn)
      listeners.set(type, set)
    },
    removeEventListener(
      type: string,
      listener: EventListenerOrEventListenerObject,
    ) {
      listeners.get(type)?.delete(listener as Listener)
    },
    emit(type: string, event: Event) {
      listeners.get(type)?.forEach((listener) => listener(event))
    },
    open() {
      this.emit("open", new Event("open"))
    },
    message(payload: object) {
      this.emit(
        "message",
        new MessageEvent("message", { data: JSON.stringify(payload) }),
      )
    },
  }
  return socket
}

describe("connectProjectSocket", () => {
  it("sends an auth frame on open and replies to ping", () => {
    const fake = createFakeSocket()
    const messages: SocketMessage[] = []
    const stop = connectProjectSocket(
      "p1",
      "token-1",
      { onMessage: (message) => messages.push(message) },
      { createSocket: () => fake, wsBaseUrl: "ws://test/api/v1" },
    )
    fake.open()
    expect(JSON.parse(fake.sent[0])).toEqual({ type: "auth", token: "token-1" })
    fake.message({ type: "ping" })
    expect(JSON.parse(fake.sent[1])).toEqual({ type: "pong" })
    fake.message({ type: "task_changed", task_id: "t1", action: "updated" })
    expect(messages).toEqual([
      { type: "task_changed", task_id: "t1", action: "updated" },
    ])
    stop()
  })

  it("reconnects after an unexpected close and notifies handlers", () => {
    vi.useFakeTimers()
    const first = createFakeSocket()
    const second = createFakeSocket()
    const sockets = [first, second]
    const statuses: string[] = []
    let reconnected = 0
    const stop = connectProjectSocket(
      "p1",
      "token-1",
      {
        onMessage: () => undefined,
        onReconnect: () => {
          reconnected += 1
        },
        onStatus: (status) => statuses.push(status),
      },
      {
        createSocket: () => sockets.shift() ?? createFakeSocket(),
        wsBaseUrl: "ws://test/api/v1",
        reconnectBaseMs: 10,
      },
    )
    first.open()
    first.close(1006)
    vi.advanceTimersByTime(10)
    second.open()
    expect(reconnected).toBe(1)
    expect(statuses).toContain("reconnecting")
    expect(statuses).toContain("connected")
    stop()
    vi.useRealTimers()
  })
})
