import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { TASK_STATUSES, type TaskStatus } from "@/types/task"

import { STATUS_LABEL } from "./StatusBadge"

export function StatusSelect({
  value,
  disabled,
  onChange,
}: {
  value: TaskStatus
  disabled?: boolean
  onChange: (status: TaskStatus) => void
}) {
  return (
    <Select
      value={value}
      disabled={disabled}
      onValueChange={(next) => onChange(next as TaskStatus)}
    >
      <SelectTrigger
        size="sm"
        className="w-[8.5rem]"
        aria-label="Change task status"
        onClick={(event) => event.stopPropagation()}
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {TASK_STATUSES.map((status) => (
          <SelectItem key={status} value={status}>
            {STATUS_LABEL[status]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
