import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"

import { handleMutationError, toastSuccess } from "@/lib/feedback"
import { queryKeys } from "@/lib/queryKeys"
import type { ProjectCreate, ProjectMemberAdd, ProjectUpdate } from "@/types/project"

import {
  addProjectMember,
  createProject,
  deleteProject,
  getProject,
  listProjects,
  removeProjectMember,
  updateProject,
} from "./api"

export function useProjects(page: number, pageSize = 12) {
  return useQuery({
    queryKey: queryKeys.projects.list(page, pageSize),
    queryFn: () => listProjects(page, pageSize),
  })
}

export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.projects.detail(projectId ?? ""),
    queryFn: () => getProject(projectId!),
    enabled: Boolean(projectId),
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: ProjectCreate) => createProject(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.all })
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats })
      toastSuccess("Project created")
    },
    onError: (error) =>
      handleMutationError(error, {
        fallback: "Could not create project",
        invalidateQueryKey: queryKeys.projects.all,
      }),
  })
}

export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: ProjectUpdate) => updateProject(projectId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.detail(projectId),
      })
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.all })
      toastSuccess("Project updated")
    },
    onError: (error) =>
      handleMutationError(error, {
        fallback: "Could not update project",
        invalidateQueryKey: queryKeys.projects.detail(projectId),
      }),
  })
}

export function useDeleteProject(projectId: string) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: () => deleteProject(projectId),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: queryKeys.projects.detail(projectId) })
      queryClient.removeQueries({
        queryKey: ["projects", projectId, "tasks"],
      })
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.all })
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.stats })
      toastSuccess("Project deleted")
      void navigate("/projects")
    },
    onError: (error) =>
      handleMutationError(error, {
        fallback: "Could not delete project",
        invalidateQueryKey: queryKeys.projects.detail(projectId),
      }),
  })
}

export function useAddProjectMember(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: ProjectMemberAdd) => addProjectMember(projectId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.detail(projectId),
      })
      toastSuccess("Member added")
    },
    onError: (error) =>
      handleMutationError(error, {
        fallback: "Could not add member",
        invalidateQueryKey: queryKeys.projects.detail(projectId),
      }),
  })
}

export function useRemoveProjectMember(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: string) => removeProjectMember(projectId, userId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.detail(projectId),
      })
      toastSuccess("Member removed")
    },
    onError: (error) =>
      handleMutationError(error, {
        fallback: "Could not remove member",
        invalidateQueryKey: queryKeys.projects.detail(projectId),
      }),
  })
}
