export type AuditEventType =
  | "LOGIN"
  | "LOGOUT"
  | "TOKEN_REUSE_DETECTED"
  | "PROJECT_CREATED"
  | "PROJECT_UPDATED"
  | "PROJECT_DELETED"
  | "MEMBER_ADDED"
  | "MEMBER_REMOVED"
  | "TASK_DELETED"
  | "TASK_COMPLETED"
  | "ATTACHMENT_UPLOADED"
  | "ATTACHMENT_DELETED"

export type AuditLog = {
  id: string
  actor_id: string | null
  actor: {
    id: string
    email: string
    full_name: string
    created_at: string
  } | null
  event_type: AuditEventType
  project_id: string | null
  resource_type: string | null
  resource_id: string | null
  metadata: Record<string, unknown> | null
  ip_address: string | null
  created_at: string
}

export type AuditPage = {
  items: AuditLog[]
  total: number
  page: number
  page_size: number
}
