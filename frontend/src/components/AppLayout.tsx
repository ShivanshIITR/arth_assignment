import { FolderKanban, LayoutDashboard, LogOut } from "lucide-react"
import { NavLink, Outlet } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { useLogout } from "@/features/auth/hooks"
import { useAuthStore } from "@/features/auth/store"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/projects", label: "Projects", icon: FolderKanban, end: false },
]

export function AppLayout() {
  const user = useAuthStore((state) => state.user)
  const logout = useLogout()

  return (
    <div className="flex min-h-svh bg-muted/30">
      <aside className="flex w-60 shrink-0 flex-col border-r bg-card">
        <div className="px-5 py-5">
          <p className="text-sm font-semibold tracking-tight">Project Manager</p>
          <p className="text-muted-foreground text-xs">Team workspace</p>
        </div>
        <nav className="flex flex-1 flex-col gap-1 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-muted font-medium text-foreground"
                    : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
                )
              }
            >
              <item.icon className="size-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t p-4">
          <p className="truncate text-sm font-medium">{user?.full_name}</p>
          <p className="truncate text-xs text-muted-foreground">{user?.email}</p>
          <Button
            type="button"
            variant="ghost"
            className="mt-3 w-full justify-start"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
          >
            <LogOut className="size-4" />
            {logout.isPending ? "Signing out…" : "Sign out"}
          </Button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 p-8">
        <Outlet />
      </main>
    </div>
  )
}
