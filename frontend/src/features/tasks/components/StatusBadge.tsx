import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { TaskPriority, TaskStatus } from "@/types/task"

const STATUS_LABEL: Record<TaskStatus, string> = {
  todo: "To do",
  in_progress: "In progress",
  completed: "Completed",
}

const PRIORITY_LABEL: Record<TaskPriority, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
}

const STATUS_CLASS: Record<TaskStatus, string> = {
  todo: "bg-slate-100 text-slate-800",
  in_progress: "bg-amber-100 text-amber-900",
  completed: "bg-emerald-100 text-emerald-900",
}

const PRIORITY_CLASS: Record<TaskPriority, string> = {
  low: "border-border text-muted-foreground",
  medium: "border-sky-200 text-sky-800",
  high: "border-red-200 text-red-800",
}

export function StatusBadge({ status }: { status: TaskStatus }) {
  return (
    <Badge className={cn("font-medium", STATUS_CLASS[status])} variant="secondary">
      {STATUS_LABEL[status]}
    </Badge>
  )
}

export function PriorityBadge({ priority }: { priority: TaskPriority }) {
  return (
    <Badge variant="outline" className={PRIORITY_CLASS[priority]}>
      {PRIORITY_LABEL[priority]}
    </Badge>
  )
}

export { STATUS_LABEL, PRIORITY_LABEL }
