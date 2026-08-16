import { Shield } from "lucide-react"

import { EmptyState, ErrorPanel } from "@/components/QueryState"
import { Skeleton } from "@/components/ui/skeleton"
import { formatAuditSentence } from "@/features/audit/format"
import { useProjectAuditLog } from "@/features/audit/hooks"
import { getApiErrorMessage } from "@/lib/apiError"
import { formatDateTime } from "@/lib/dates"

export function AuditLogPanel({ projectId }: { projectId: string }) {
  const query = useProjectAuditLog(projectId)

  if (query.isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-16 w-full" />
      </div>
    )
  }

  if (query.isError) {
    return (
      <ErrorPanel
        title="Could not load audit log"
        message={getApiErrorMessage(query.error, "Audit log is unavailable")}
        onRetry={() => void query.refetch()}
      />
    )
  }

  const items = query.data?.items ?? []

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-2">
        <Shield className="size-4 text-muted-foreground" />
        <h2 className="text-lg font-medium">Audit log</h2>
      </div>
      {items.length === 0 ? (
        <EmptyState
          title="No audit events yet"
          description="Significant project actions will appear here for owners."
        />
      ) : (
        <ol className="space-y-3">
          {items.map((entry) => (
            <li
              key={entry.id}
              className="rounded-xl border bg-card px-4 py-3 text-sm"
            >
              <p>{formatAuditSentence(entry)}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatDateTime(entry.created_at)}
                {entry.ip_address ? ` · ${entry.ip_address}` : ""}
              </p>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
