import { useEffect, useState } from "react"

import { PaginationBar } from "@/components/PaginationBar"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { getApiErrorMessage } from "@/lib/apiError"
import type { TaskPriority, TaskStatus } from "@/types/task"

import { TaskBoard } from "./components/TaskBoard"
import { TaskFilterBar } from "./components/TaskFilterBar"
import { useTasks } from "./hooks"

const PAGE_SIZE = 20

export function ProjectTaskSection({ projectId }: { projectId: string }) {
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState<TaskStatus | undefined>()
  const [priority, setPriority] = useState<TaskPriority | undefined>()
  const [page, setPage] = useState(1)
  const debouncedSearch = useDebouncedValue(search, 300)

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
        <div className="rounded-xl border bg-card p-6">
          <p className="font-medium">Could not load tasks</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {getApiErrorMessage(tasks.error)}
          </p>
          <Button
            type="button"
            className="mt-3"
            variant="outline"
            onClick={() => void tasks.refetch()}
          >
            Retry
          </Button>
        </div>
      ) : null}

      {tasks.data && tasks.data.items.length === 0 ? (
        <div className="rounded-xl border border-dashed bg-card p-10 text-center">
          <p className="font-medium">No tasks yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Create one to start tracking work in this project.
          </p>
        </div>
      ) : null}

      {tasks.data && tasks.data.items.length > 0 ? (
        <>
          <TaskBoard tasks={tasks.data.items} />
          <PaginationBar
            page={tasks.data.page}
            pageSize={tasks.data.page_size}
            total={tasks.data.total}
            onPageChange={setPage}
          />
        </>
      ) : null}
    </section>
  )
}
