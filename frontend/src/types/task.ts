import type { components } from "./api.generated"

export type Task = components["schemas"]["TaskRead"]
export type TaskCreate = components["schemas"]["TaskCreate"]
export type TaskUpdate = components["schemas"]["TaskUpdate"]
export type TaskStatus = components["schemas"]["TaskStatus"]
export type TaskPriority = components["schemas"]["TaskPriority"]
export type TaskPage = components["schemas"]["Page_TaskRead_"]
export type DashboardStats = components["schemas"]["DashboardStats"]

export const TASK_STATUSES: TaskStatus[] = ["todo", "in_progress", "completed"]
export const TASK_PRIORITIES: TaskPriority[] = ["low", "medium", "high"]
