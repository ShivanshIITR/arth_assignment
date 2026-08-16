export type LiveStatus = "connected" | "reconnecting" | "disconnected"

export type SocketMessage = {
  type: string
  task_id?: string
  action?: string
}

export type ProjectSocketHandlers = {
  onMessage: (message: SocketMessage) => void
  onReconnect?: () => void
  onStatus?: (status: LiveStatus) => void
}

export type SocketFactory = (url: string) => Pick<
  WebSocket,
  "send" | "close" | "addEventListener" | "removeEventListener" | "readyState"
>

export function websocketBaseUrl(): string {
  const configured = import.meta.env.VITE_WS_URL
  if (configured) {
    return configured.replace(/\/$/, "")
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
  return `${protocol}//${window.location.host}/api/v1`
}

export function connectProjectSocket(
  projectId: string,
  token: string,
  handlers: ProjectSocketHandlers,
  options?: {
    createSocket?: SocketFactory
    wsBaseUrl?: string
    reconnectBaseMs?: number
    maxReconnectMs?: number
  },
): () => void {
  const createSocket = options?.createSocket ?? ((url: string) => new WebSocket(url))
  const baseUrl = options?.wsBaseUrl ?? websocketBaseUrl()
  const reconnectBaseMs = options?.reconnectBaseMs ?? 1000
  const maxReconnectMs = options?.maxReconnectMs ?? 30_000
  const url = `${baseUrl}/ws/projects/${projectId}`

  let disposed = false
  let socket: ReturnType<SocketFactory> | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let attempt = 0
  let hasConnected = false

  function setStatus(status: LiveStatus) {
    handlers.onStatus?.(status)
  }

  function clearTimer() {
    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function open() {
    if (disposed) {
      return
    }
    try {
      socket = createSocket(url)
    } catch {
      setStatus("disconnected")
      return
    }
    socket.addEventListener("open", () => {
      if (disposed) {
        return
      }
      socket?.send(JSON.stringify({ type: "auth", token }))
      setStatus("connected")
      if (hasConnected) {
        handlers.onReconnect?.()
      }
      hasConnected = true
      attempt = 0
    })
    socket.addEventListener("message", (event: Event) => {
      const text = (event as MessageEvent).data
      if (typeof text !== "string") {
        return
      }
      let payload: SocketMessage
      try {
        payload = JSON.parse(text) as SocketMessage
      } catch {
        return
      }
      if (payload.type === "ping") {
        socket?.send(JSON.stringify({ type: "pong" }))
        return
      }
      handlers.onMessage(payload)
    })
    socket.addEventListener("close", (event: Event) => {
      const code = (event as CloseEvent).code
      socket = null
      if (disposed || code === 4401 || code === 4403) {
        setStatus("disconnected")
        return
      }
      setStatus("reconnecting")
      const delay = Math.min(reconnectBaseMs * 2 ** attempt, maxReconnectMs)
      attempt += 1
      reconnectTimer = setTimeout(open, delay)
    })
  }

  open()

  return () => {
    disposed = true
    clearTimer()
    socket?.close()
    socket = null
    setStatus("disconnected")
  }
}
