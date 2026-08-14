import { Link } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { getApiErrorMessage } from "@/lib/apiError"

import { StatCard } from "./components/StatCard"
import { useDashboardStats } from "./hooks"

export function DashboardPage() {
  const stats = useDashboardStats()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Aggregates across projects you belong to.
        </p>
      </div>

      {stats.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {Array.from({ length: 5 }).map((_, index) => (
            <Skeleton key={index} className="h-28 rounded-xl" />
          ))}
        </div>
      ) : null}

      {stats.isError ? (
        <div className="rounded-xl border bg-card p-6">
          <p className="font-medium">Could not load dashboard stats</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {getApiErrorMessage(stats.error)}
          </p>
          <Button
            type="button"
            className="mt-3"
            variant="outline"
            onClick={() => void stats.refetch()}
          >
            Retry
          </Button>
        </div>
      ) : null}

      {stats.data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <StatCard label="Total projects" value={stats.data.total_projects} />
            <StatCard
              label="Active projects"
              value={stats.data.active_projects}
              hint="Projects with at least one incomplete task"
            />
            <StatCard label="Total tasks" value={stats.data.total_tasks} />
            <StatCard
              label="Completed tasks"
              value={stats.data.completed_tasks}
            />
            <StatCard label="Pending tasks" value={stats.data.pending_tasks} />
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard
              label="To do"
              value={stats.data.tasks_by_status.todo ?? 0}
            />
            <StatCard
              label="In progress"
              value={stats.data.tasks_by_status.in_progress ?? 0}
            />
            <StatCard
              label="Completed"
              value={stats.data.tasks_by_status.completed ?? 0}
            />
          </div>
          {stats.data.total_projects === 0 ? (
            <div className="rounded-xl border border-dashed bg-card p-8 text-center">
              <p className="font-medium">No projects yet</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Create a project to see activity here.
              </p>
              <Button asChild className="mt-4">
                <Link to="/projects">Go to projects</Link>
              </Button>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  )
}
