import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"
import type { TaskPriority, TaskStatus } from "@/types/task"

import { listTasks } from "./api"

export type TaskQueryFilters = {
  status?: TaskStatus
  priority?: TaskPriority
  search: string
  page: number
  pageSize: number
}

export function useTasks(projectId: string | undefined, filters: TaskQueryFilters) {
  return useQuery({
    queryKey: queryKeys.projects.tasks(projectId ?? "", filters),
    queryFn: () =>
      listTasks(projectId!, {
        status: filters.status,
        priority: filters.priority,
        search: filters.search,
        page: filters.page,
        pageSize: filters.pageSize,
      }),
    enabled: Boolean(projectId),
  })
}
