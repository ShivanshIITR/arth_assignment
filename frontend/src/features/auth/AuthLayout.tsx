import { Link } from "react-router-dom"
import type { ReactNode } from "react"

export function AuthLayout({
  title,
  description,
  children,
}: {
  title: string
  description: string
  children: ReactNode
}) {
  return (
    <div className="flex min-h-svh items-center justify-center bg-muted/40 p-6">
      <div className="w-full max-w-md rounded-xl border bg-card p-8 shadow-sm">
        <Link to="/" className="text-sm font-medium text-muted-foreground">
          Project Manager
        </Link>
        <h1 className="mt-4 text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        <div className="mt-6">{children}</div>
      </div>
    </div>
  )
}
