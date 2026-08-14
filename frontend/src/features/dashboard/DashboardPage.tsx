import { Link } from "react-router-dom"

import { EmptyState, ErrorPanel } from "@/components/QueryState"
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
        <ErrorPanel
          title="Could not load dashboard stats"
          message={getApiErrorMessage(stats.error)}
          onRetry={() => void stats.refetch()}
        />
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
            <EmptyState
              title="No projects yet"
              description="Create a project to see activity here."
              action={
                <Button asChild>
                  <Link to="/projects">Go to projects</Link>
                </Button>
              }
            />
          ) : null}
        </>
      ) : null}
    </div>
  )
}
