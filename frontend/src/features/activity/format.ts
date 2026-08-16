import type { ActivityLog } from "@/types/activity"

function actorName(entry: ActivityLog): string {
  return entry.actor?.full_name ?? "Someone"
}

function metaString(entry: ActivityLog, key: string): string | undefined {
  const value = entry.metadata?.[key]
  return typeof value === "string" ? value : undefined
}

function metaNumber(entry: ActivityLog, key: string): number | undefined {
  const value = entry.metadata?.[key]
  return typeof value === "number" ? value : undefined
}

const STATUS_LABELS: Record<string, string> = {
  todo: "Todo",
  in_progress: "In progress",
  completed: "Completed",
}

export function formatActivitySentence(entry: ActivityLog): string {
  const name = actorName(entry)
  switch (entry.event_type) {
    case "PROJECT_CREATED":
      return `${name} created the project`
    case "PROJECT_UPDATED":
      return `${name} updated the project`
    case "MEMBER_ADDED":
      return `${name} added a member`
    case "MEMBER_REMOVED":
      return `${name} removed a member`
    case "TASK_CREATED":
      return `${name} created a task`
    case "TASK_ASSIGNED":
      return `${name} assigned a task`
    case "TASK_STATUS_CHANGED": {
      const from = STATUS_LABELS[metaString(entry, "old_status") ?? ""] ?? "a status"
      const to = STATUS_LABELS[metaString(entry, "new_status") ?? ""] ?? "another status"
      return `${name} changed a task from ${from} to ${to}`
    }
    case "TASK_UPDATED":
      return `${name} updated a task`
    case "TASK_DELETED":
      return `${name} deleted a task`
    case "TASK_REASSIGNED": {
      const count = metaNumber(entry, "task_count") ?? 0
      return `${count} task${count === 1 ? "" : "s"} reassigned to the project owner`
    }
    case "ATTACHMENT_UPLOADED":
      return `${name} uploaded an attachment`
    case "ATTACHMENT_DELETED":
      return `${name} deleted an attachment`
  }
}
