import { useEffect, useState, type ReactNode } from "react"

import { getCurrentUser, refreshSession } from "./api"
import { useAuthStore } from "./store"

export function AuthProvider({ children }: { children: ReactNode }) {
  const [bootstrapped, setBootstrapped] = useState(false)
  const setSession = useAuthStore((state) => state.setSession)
  const setAccessToken = useAuthStore((state) => state.setAccessToken)
  const clear = useAuthStore((state) => state.clear)

  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      try {
        const tokens = await refreshSession()
        if (cancelled) {
          return
        }
        setAccessToken(tokens.access_token)
        const user = await getCurrentUser()
        if (cancelled) {
          return
        }
        setSession(tokens.access_token, user)
      } catch {
        if (!cancelled) {
          clear()
        }
      } finally {
        if (!cancelled) {
          setBootstrapped(true)
        }
      }
    }

    void bootstrap()
    return () => {
      cancelled = true
    }
  }, [clear, setAccessToken, setSession])

  if (!bootstrapped) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <div className="text-muted-foreground text-sm">Restoring session…</div>
      </div>
    )
  }

  return children
}
