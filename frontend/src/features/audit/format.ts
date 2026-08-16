import type { AuditLog } from "@/types/audit"

function actorName(entry: AuditLog): string {
  return entry.actor?.full_name ?? "Someone"
}

export function formatAuditSentence(entry: AuditLog): string {
  const name = actorName(entry)
  switch (entry.event_type) {
    case "LOGIN":
      return `${name} signed in`
    case "LOGOUT":
      return `${name} signed out`
    case "TOKEN_REUSE_DETECTED":
      return `Refresh token reuse detected for ${name}`
    case "PROJECT_CREATED":
      return `${name} created the project`
    case "PROJECT_UPDATED":
      return `${name} updated the project`
    case "PROJECT_DELETED":
      return `${name} deleted the project`
    case "MEMBER_ADDED":
      return `${name} added a member`
    case "MEMBER_REMOVED":
      return `${name} removed a member`
    case "TASK_DELETED":
      return `${name} deleted a task`
    case "TASK_COMPLETED":
      return `${name} completed a task`
    case "ATTACHMENT_UPLOADED":
      return `${name} uploaded an attachment`
    case "ATTACHMENT_DELETED":
      return `${name} deleted an attachment`
  }
}
