import { formatDate } from "@/lib/dates"
import type { Task } from "@/types/task"

import { PriorityBadge, StatusBadge } from "./StatusBadge"

export function TaskCard({ task }: { task: Task }) {
  return (
    <article className="rounded-lg border bg-card p-3 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium leading-snug">{task.title}</h3>
        <StatusBadge status={task.status} />
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <PriorityBadge priority={task.priority} />
        <span>{task.assignee?.full_name ?? "Unassigned"}</span>
        <span>Due {formatDate(task.due_date)}</span>
      </div>
    </article>
  )
}
