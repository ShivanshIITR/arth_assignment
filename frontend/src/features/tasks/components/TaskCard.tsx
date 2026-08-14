import { Link } from "react-router-dom"
import type { ReactNode } from "react"

import { formatDate } from "@/lib/dates"
import type { Task, TaskStatus } from "@/types/task"

import { PriorityBadge } from "./StatusBadge"
import { StatusSelect } from "./StatusSelect"

export function TaskCard({
  task,
  onStatusChange,
  statusPending = false,
  dragHandle,
}: {
  task: Task
  onStatusChange?: (status: TaskStatus) => void
  statusPending?: boolean
  dragHandle?: ReactNode
}) {
  return (
    <article className="rounded-lg border bg-card p-3 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-start gap-2">
          {dragHandle}
          <Link
            to={`/projects/${task.project_id}/tasks/${task.id}`}
            className="text-sm font-medium leading-snug hover:underline"
          >
            {task.title}
          </Link>
        </div>
        {onStatusChange ? (
          <StatusSelect
            value={task.status}
            disabled={statusPending}
            onChange={onStatusChange}
          />
        ) : null}
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <PriorityBadge priority={task.priority} />
        <span>{task.assignee?.full_name ?? "Unassigned"}</span>
        <span>Due {formatDate(task.due_date)}</span>
      </div>
    </article>
  )
}
