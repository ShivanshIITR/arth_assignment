export type ActivityEventType =
  | "PROJECT_CREATED"
  | "PROJECT_UPDATED"
  | "MEMBER_ADDED"
  | "MEMBER_REMOVED"
  | "TASK_CREATED"
  | "TASK_ASSIGNED"
  | "TASK_STATUS_CHANGED"
  | "TASK_UPDATED"
  | "TASK_DELETED"
  | "TASK_REASSIGNED"
  | "ATTACHMENT_UPLOADED"
  | "ATTACHMENT_DELETED"

export type ActivityActor = {
  id: string
  email: string
  full_name: string
  created_at: string
}

export type ActivityLog = {
  id: string
  project_id: string
  actor_id: string | null
  actor: ActivityActor | null
  event_type: ActivityEventType
  task_id: string | null
  metadata: Record<string, unknown> | null
  created_at: string
}

export type ActivityPage = {
  items: ActivityLog[]
  total: number
  page: number
  page_size: number
}
