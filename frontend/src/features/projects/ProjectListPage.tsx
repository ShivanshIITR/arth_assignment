import { useState } from "react"

import { PaginationBar } from "@/components/PaginationBar"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"

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
        <div className="rounded-xl border bg-card p-6">
          <p className="font-medium">Could not load projects</p>
          <Button
            type="button"
            className="mt-3"
            variant="outline"
            onClick={() => void projects.refetch()}
          >
            Retry
          </Button>
        </div>
      ) : null}

      {projects.data && projects.data.items.length === 0 ? (
        <div className="rounded-xl border border-dashed bg-card p-10 text-center">
          <p className="font-medium">No projects yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Create a project to start tracking tasks.
          </p>
          <Button
            type="button"
            className="mt-4"
            onClick={() => setCreateOpen(true)}
          >
            Create project
          </Button>
        </div>
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
