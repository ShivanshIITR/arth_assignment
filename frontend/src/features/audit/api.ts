import { apiClient } from "@/lib/apiClient"
import type { AuditPage } from "@/types/audit"

export async function getProjectAuditLogs(
  projectId: string,
  page = 1,
  pageSize = 20,
): Promise<AuditPage> {
  const { data } = await apiClient.get<AuditPage>(
    `/projects/${projectId}/audit-logs`,
    { params: { page, page_size: pageSize } },
  )
  return data
}

export async function getMyAuditLogs(
  page = 1,
  pageSize = 20,
): Promise<AuditPage> {
  const { data } = await apiClient.get<AuditPage>("/users/me/audit-logs", {
    params: { page, page_size: pageSize },
  })
  return data
}
