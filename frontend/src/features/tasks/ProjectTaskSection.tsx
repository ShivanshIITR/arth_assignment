import { useEffect, useState } from "react"

import { PaginationBar } from "@/components/PaginationBar"
import { EmptyState, ErrorPanel } from "@/components/QueryState"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { getApiErrorMessage } from "@/lib/apiError"
import type { ProjectMember } from "@/types/project"
import type { TaskPriority, TaskStatus } from "@/types/task"

import { CreateTaskDialog } from "./components/CreateTaskDialog"
import { TaskBoard } from "./components/TaskBoard"
import { TaskFilterBar } from "./components/TaskFilterBar"
import { useTasks, useUpdateTaskStatus } from "./hooks"

const PAGE_SIZE = 20

export function ProjectTaskSection({
  projectId,
  members,
}: {
  projectId: string
  members: ProjectMember[]
}) {
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState<TaskStatus | undefined>()
  const [priority, setPriority] = useState<TaskPriority | undefined>()
  const [page, setPage] = useState(1)
  const [createOpen, setCreateOpen] = useState(false)
  const debouncedSearch = useDebouncedValue(search, 300)
  const updateStatus = useUpdateTaskStatus(projectId)

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, status, priority])

  const tasks = useTasks(projectId, {
    search: debouncedSearch.trim(),
    status,
    priority,
    page,
    pageSize: PAGE_SIZE,
  })

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Tasks</h2>
        <Button type="button" onClick={() => setCreateOpen(true)}>
          New task
        </Button>
      </div>
      <TaskFilterBar
        value={{ search, status, priority }}
        onChange={(next) => {
          setSearch(next.search)
          setStatus(next.status)
          setPriority(next.priority)
        }}
      />

      {tasks.isLoading ? (
        <div className="grid gap-4 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-48 rounded-xl" />
          ))}
        </div>
      ) : null}

      {tasks.isError ? (
        <ErrorPanel
          title="Could not load tasks"
          message={getApiErrorMessage(tasks.error)}
          onRetry={() => void tasks.refetch()}
        />
      ) : null}

      {tasks.data && tasks.data.items.length === 0 ? (
        <EmptyState
          title="No tasks yet"
          description="Create one to start tracking work in this project."
          action={
            <Button type="button" onClick={() => setCreateOpen(true)}>
              Create task
            </Button>
          }
        />
      ) : null}

      {updateStatus.isError ? (
        <p className="text-sm text-destructive">
          {getApiErrorMessage(updateStatus.error, "Could not change status")}
        </p>
      ) : null}

      {tasks.data && tasks.data.items.length > 0 ? (
        <>
          <TaskBoard
            tasks={tasks.data.items}
            pendingTaskId={
              updateStatus.isPending
                ? updateStatus.variables?.taskId
                : undefined
            }
            onStatusChange={(taskId, nextStatus) =>
              updateStatus.mutate({ taskId, status: nextStatus })
            }
          />
          <PaginationBar
            page={tasks.data.page}
            pageSize={tasks.data.page_size}
            total={tasks.data.total}
            onPageChange={setPage}
          />
        </>
      ) : null}

      <CreateTaskDialog
        projectId={projectId}
        members={members}
        open={createOpen}
        onOpenChange={setCreateOpen}
      />
    </section>
  )
}
