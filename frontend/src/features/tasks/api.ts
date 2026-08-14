import { apiClient } from "@/lib/apiClient"
import type { Task, TaskCreate, TaskPage, TaskPriority, TaskStatus, TaskUpdate } from "@/types/task"

export type TaskListFilters = {
  status?: TaskStatus
  priority?: TaskPriority
  search?: string
  page?: number
  pageSize?: number
}

export async function listTasks(
  projectId: string,
  filters: TaskListFilters = {},
): Promise<TaskPage> {
  const { data } = await apiClient.get<TaskPage>(
    `/projects/${projectId}/tasks`,
    {
      params: {
        page: filters.page ?? 1,
        page_size: filters.pageSize ?? 20,
        status: filters.status,
        priority: filters.priority,
        search: filters.search || undefined,
      },
    },
  )
  return data
}

export async function getTask(taskId: string): Promise<Task> {
  const { data } = await apiClient.get<Task>(`/tasks/${taskId}`)
  return data
}

export async function createTask(
  projectId: string,
  body: TaskCreate,
): Promise<Task> {
  const { data } = await apiClient.post<Task>(
    `/projects/${projectId}/tasks`,
    body,
  )
  return data
}

export async function updateTask(
  taskId: string,
  body: TaskUpdate,
): Promise<Task> {
  const { data } = await apiClient.patch<Task>(`/tasks/${taskId}`, body)
  return data
}

export async function deleteTask(taskId: string): Promise<void> {
  await apiClient.delete(`/tasks/${taskId}`)
}
