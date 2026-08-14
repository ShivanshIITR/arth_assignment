import { apiClient } from "@/lib/apiClient"
import type { TaskPage, TaskPriority, TaskStatus } from "@/types/task"

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
