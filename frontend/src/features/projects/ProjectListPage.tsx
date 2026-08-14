import { useState } from "react"

import { PaginationBar } from "@/components/PaginationBar"
import { EmptyState, ErrorPanel } from "@/components/QueryState"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { getApiErrorMessage } from "@/lib/apiError"

import { ProjectCard } from "./components/ProjectCard"
import { CreateProjectDialog } from "./components/CreateProjectDialog"
import { useProjects } from "./hooks"

const PAGE_SIZE = 12

export function ProjectListPage() {
  const [page, setPage] = useState(1)
  const [createOpen, setCreateOpen] = useState(false)
  const projects = useProjects(page, PAGE_SIZE)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Projects</h1>
          <p className="text-sm text-muted-foreground">
            Projects you own or belong to.
          </p>
        </div>
        <Button type="button" onClick={() => setCreateOpen(true)}>
          New project
        </Button>
      </div>

      {projects.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} className="h-36 rounded-xl" />
          ))}
        </div>
      ) : null}

      {projects.isError ? (
        <ErrorPanel
          title="Could not load projects"
          message={getApiErrorMessage(projects.error)}
          onRetry={() => void projects.refetch()}
        />
      ) : null}

      {projects.data && projects.data.items.length === 0 ? (
        <EmptyState
          title="No projects yet"
          description="Create a project to start tracking tasks."
          action={
            <Button type="button" onClick={() => setCreateOpen(true)}>
              Create project
            </Button>
          }
        />
      ) : null}

      {projects.data && projects.data.items.length > 0 ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {projects.data.items.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
          <PaginationBar
            page={projects.data.page}
            pageSize={projects.data.page_size}
            total={projects.data.total}
            onPageChange={setPage}
          />
        </>
      ) : null}

      <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  )
}
