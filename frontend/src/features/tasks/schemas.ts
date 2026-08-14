import { z } from "zod"

import { TASK_PRIORITIES, TASK_STATUSES } from "@/types/task"

export const taskFormSchema = z.object({
  title: z.string().min(1, "Title is required").max(255, "Title is too long"),
  description: z.string().max(8000, "Description is too long").optional(),
  status: z.enum(TASK_STATUSES),
  priority: z.enum(TASK_PRIORITIES),
  assignee_id: z.string().optional(),
  due_date: z.string().optional(),
})

export type TaskFormValues = z.infer<typeof taskFormSchema>

export function emptyToNull(value: string | undefined): string | null {
  const trimmed = value?.trim()
  return trimmed ? trimmed : null
}

export function canCompleteTask(values: {
  title?: string | null
  assignee_id?: string | null
  priority?: string | null
  due_date?: string | null
}): boolean {
  return Boolean(
    values.title?.trim() &&
      values.assignee_id &&
      values.priority &&
      values.due_date,
  )
}
