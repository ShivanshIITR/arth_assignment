import { Activity, LoaderCircle } from "lucide-react"

import { EmptyState, ErrorPanel } from "@/components/QueryState"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useProjectActivity } from "@/features/activity/hooks"
import { formatActivitySentence } from "@/features/activity/format"
import { formatDateTime } from "@/lib/dates"
import { getApiErrorMessage } from "@/lib/apiError"

export function ActivityFeed({ projectId }: { projectId: string }) {
  const query = useProjectActivity(projectId)
  const entries = query.data?.pages.flatMap((page) => page.items) ?? []

  if (query.isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    )
  }

  if (query.isError) {
    return (
      <ErrorPanel
        title="Could not load activity"
        message={getApiErrorMessage(query.error, "Activity is unavailable")}
        onRetry={() => void query.refetch()}
      />
    )
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-2">
        <Activity className="size-4 text-muted-foreground" />
        <h2 className="text-lg font-medium">Activity</h2>
      </div>
      {entries.length === 0 ? (
        <EmptyState
          title="No activity yet"
          description="Project changes will show up here as they happen."
        />
      ) : (
        <ol className="space-y-3">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className="rounded-xl border bg-card px-4 py-3 text-sm"
            >
              <p>{formatActivitySentence(entry)}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatDateTime(entry.created_at)}
              </p>
            </li>
          ))}
        </ol>
      )}
      {query.hasNextPage ? (
        <Button
          type="button"
          variant="outline"
          onClick={() => void query.fetchNextPage()}
          disabled={query.isFetchingNextPage}
        >
          {query.isFetchingNextPage ? (
            <LoaderCircle className="size-4 animate-spin" />
          ) : null}
          Load more
        </Button>
      ) : null}
    </section>
  )
}
