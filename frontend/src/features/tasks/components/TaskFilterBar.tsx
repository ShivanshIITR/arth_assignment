import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { TASK_PRIORITIES, TASK_STATUSES, type TaskPriority, type TaskStatus } from "@/types/task"

import { PRIORITY_LABEL, STATUS_LABEL } from "./StatusBadge"

type Filters = {
  search: string
  status?: TaskStatus
  priority?: TaskPriority
}

export function TaskFilterBar({
  value,
  onChange,
}: {
  value: Filters
  onChange: (next: Filters) => void
}) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <Input
        value={value.search}
        onChange={(event) => onChange({ ...value, search: event.target.value })}
        placeholder="Search tasks"
        className="max-w-xs"
        aria-label="Search tasks"
      />
      <Select
        value={value.status ?? "all"}
        onValueChange={(status) =>
          onChange({
            ...value,
            status: status === "all" ? undefined : (status as TaskStatus),
          })
        }
      >
        <SelectTrigger className="w-40" aria-label="Filter by status">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All statuses</SelectItem>
          {TASK_STATUSES.map((status) => (
            <SelectItem key={status} value={status}>
              {STATUS_LABEL[status]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select
        value={value.priority ?? "all"}
        onValueChange={(priority) =>
          onChange({
            ...value,
            priority: priority === "all" ? undefined : (priority as TaskPriority),
          })
        }
      >
        <SelectTrigger className="w-40" aria-label="Filter by priority">
          <SelectValue placeholder="Priority" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All priorities</SelectItem>
          {TASK_PRIORITIES.map((priority) => (
            <SelectItem key={priority} value={priority}>
              {PRIORITY_LABEL[priority]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
