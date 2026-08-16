import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"

import { handleMutationError, toastSuccess } from "@/lib/feedback"
import { queryKeys } from "@/lib/queryKeys"
import type { Task, TaskCreate, TaskPage, TaskStatus, TaskUpdate } from "@/types/task"

import {
  createTask,
  deleteTask,
  getTask,
  listTasks,
  updateTask,
} from "./api"

export type TaskQueryFilters = {
  status?: TaskStatus
  priority?: Task["priority"]
  search: string
  page: number
  pageSize: number
}

export function useTasks(
  projectId: string | undefined,
  filters: TaskQueryFilters,
) {
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

export function useTask(taskId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.tasks.detail(taskId ?? ""),
    queryFn: () => getTask(taskId!),
    enabled: Boolean(taskId),
  })
}

function invalidateTaskCollections(
  queryClient: ReturnType<typeof useQueryClient>,
  projectId: string,
) {
  void queryClient.invalidateQueries({
    queryKey: ["projects", projectId, "tasks"],
  })
  void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats })
  void queryClient.invalidateQueries({
    queryKey: queryKeys.projects.activity(projectId),
  })
}

export function useCreateTask(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: TaskCreate) => createTask(projectId, body),
    onSuccess: () => {
      invalidateTaskCollections(queryClient, projectId)
      toastSuccess("Task created")
    },
    onError: (error) =>
      handleMutationError(error, {
        fallback: "Could not create task",
        invalidateQueryKey: ["projects", projectId, "tasks"],
      }),
  })
}

export function useUpdateTask(projectId: string, taskId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: TaskUpdate) => updateTask(taskId, body),
    onSuccess: (task) => {
      queryClient.setQueryData(queryKeys.tasks.detail(taskId), task)
      void queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "tasks"],
      })
      toastSuccess("Task updated")
    },
    onError: (error) =>
      handleMutationError(error, {
        fallback: "Could not update task",
        invalidateQueryKey: queryKeys.tasks.detail(taskId),
      }),
  })
}

export function useUpdateTaskStatus(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: TaskStatus }) =>
      updateTask(taskId, { status }),
    onMutate: async ({ taskId, status }) => {
      await queryClient.cancelQueries({
        queryKey: ["projects", projectId, "tasks"],
      })
      queryClient.setQueriesData<TaskPage>(
        { queryKey: ["projects", projectId, "tasks"] },
        (current) => {
          if (!current) {
            return current
          }
          return {
            ...current,
            items: current.items.map((task) =>
              task.id === taskId ? { ...task, status } : task,
            ),
          }
        },
      )
      queryClient.setQueryData<Task>(queryKeys.tasks.detail(taskId), (current) =>
        current ? { ...current, status } : current,
      )
    },
    onError: (error, variables) => {
      handleMutationError(error, {
        fallback: "Could not change status",
        invalidateQueryKey: ["projects", projectId, "tasks"],
      })
      void queryClient.invalidateQueries({
        queryKey: queryKeys.tasks.detail(variables.taskId),
      })
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats })
    },
    onSuccess: (task) => {
      queryClient.setQueryData(queryKeys.tasks.detail(task.id), task)
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats })
    },
  })
}

export function useDeleteTask(projectId: string, taskId: string) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: () => deleteTask(taskId),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: queryKeys.tasks.detail(taskId) })
      invalidateTaskCollections(queryClient, projectId)
      toastSuccess("Task deleted")
      void navigate(`/projects/${projectId}`)
    },
    onError: (error) =>
      handleMutationError(error, {
        fallback: "Could not delete task",
        invalidateQueryKey: queryKeys.tasks.detail(taskId),
      }),
  })
}
