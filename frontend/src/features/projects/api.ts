import { apiClient } from "@/lib/apiClient"
import type {
  Project,
  ProjectCreate,
  ProjectMemberAdd,
  ProjectPage,
  ProjectUpdate,
} from "@/types/project"

export async function listProjects(
  page = 1,
  pageSize = 12,
): Promise<ProjectPage> {
  const { data } = await apiClient.get<ProjectPage>("/projects", {
    params: { page, page_size: pageSize },
  })
  return data
}

export async function getProject(projectId: string): Promise<Project> {
  const { data } = await apiClient.get<Project>(`/projects/${projectId}`)
  return data
}

export async function createProject(body: ProjectCreate): Promise<Project> {
  const { data } = await apiClient.post<Project>("/projects", body)
  return data
}

export async function updateProject(
  projectId: string,
  body: ProjectUpdate,
): Promise<Project> {
  const { data } = await apiClient.patch<Project>(`/projects/${projectId}`, body)
  return data
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}`)
}

export async function addProjectMember(
  projectId: string,
  body: ProjectMemberAdd,
): Promise<Project> {
  const { data } = await apiClient.post<Project>(
    `/projects/${projectId}/members`,
    body,
  )
  return data
}

export async function removeProjectMember(
  projectId: string,
  userId: string,
): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/members/${userId}`)
}
