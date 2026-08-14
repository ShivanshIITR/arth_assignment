import { TASK_STATUSES, type Task, type TaskStatus } from "@/types/task"

import { STATUS_LABEL } from "./StatusBadge"
import { TaskCard } from "./TaskCard"

export function TaskBoard({
  tasks,
  onStatusChange,
  pendingTaskId,
}: {
  tasks: Task[]
  onStatusChange?: (taskId: string, status: TaskStatus) => void
  pendingTaskId?: string | null
}) {
  const grouped: Record<TaskStatus, Task[]> = {
    todo: [],
    in_progress: [],
    completed: [],
  }
  for (const task of tasks) {
    grouped[task.status].push(task)
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {TASK_STATUSES.map((status) => (
        <section key={status} className="rounded-xl border bg-muted/20 p-3">
          <header className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold">{STATUS_LABEL[status]}</h3>
            <span className="text-xs text-muted-foreground">
              {grouped[status].length}
            </span>
          </header>
          <div className="space-y-2">
            {grouped[status].length === 0 ? (
              <p className="px-1 py-6 text-center text-xs text-muted-foreground">
                No tasks
              </p>
            ) : (
              grouped[status].map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  statusPending={pendingTaskId === task.id}
                  onStatusChange={
                    onStatusChange
                      ? (next) => onStatusChange(task.id, next)
                      : undefined
                  }
                />
              ))
            )}
          </div>
        </section>
      ))}
    </div>
  )
}
