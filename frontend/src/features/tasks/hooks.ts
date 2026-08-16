import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"

import { useAuthStore } from "@/features/auth/store"
import { handleMutationError, toastSuccess } from "@/lib/feedback"
import { queryKeys } from "@/lib/queryKeys"
import {
  connectProjectSocket,
  type LiveStatus,
} from "@/lib/websocketClient"
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

export function useTaskLiveUpdates(projectId: string | undefined): LiveStatus {
  const queryClient = useQueryClient()
  const accessToken = useAuthStore((state) => state.accessToken)
  const [status, setStatus] = useState<LiveStatus>("disconnected")

  useEffect(() => {
    if (!projectId || !accessToken) {
      setStatus("disconnected")
      return
    }
    const id = projectId
    const token = accessToken

    function invalidateLiveQueries(taskId?: string) {
      void queryClient.invalidateQueries({
        queryKey: ["projects", id, "tasks"],
      })
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.activity(id),
      })
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats })
      if (taskId) {
        void queryClient.invalidateQueries({
          queryKey: queryKeys.tasks.detail(taskId),
        })
      }
    }

    return connectProjectSocket(id, token, {
      onStatus: setStatus,
      onReconnect: () => invalidateLiveQueries(),
      onMessage: (message) => {
        if (message.type === "task_changed") {
          invalidateLiveQueries(message.task_id)
        }
        if (message.type === "attachment_changed") {
          invalidateLiveQueries(message.task_id)
        }
      },
    })
  }, [projectId, accessToken, queryClient])

  return status
}
