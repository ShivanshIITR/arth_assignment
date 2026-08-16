import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"

import { getMyAuditLogs, getProjectAuditLogs } from "./api"

export function useProjectAuditLog(projectId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.projects.audit(projectId ?? ""),
    queryFn: () => getProjectAuditLogs(projectId!),
    enabled: Boolean(projectId),
  })
}

export function useMyAuditLog() {
  return useQuery({
    queryKey: queryKeys.audit.me,
    queryFn: () => getMyAuditLogs(),
  })
}
