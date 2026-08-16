import { useState } from "react"
import { Link, useParams } from "react-router-dom"

import { ConfirmDialog } from "@/components/ConfirmDialog"
import { ErrorPanel } from "@/components/QueryState"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuthStore } from "@/features/auth/store"
import { formatDateTime } from "@/lib/dates"
import { getApiErrorMessage } from "@/lib/apiError"

import { ActivityFeed } from "./components/ActivityFeed"
import { EditProjectDialog } from "./components/EditProjectDialog"
import { MemberList } from "./components/MemberList"
import { useDeleteProject, useProject } from "./hooks"
import { ProjectTaskSection } from "@/features/tasks/ProjectTaskSection"

export function ProjectDetailsPage() {
  const { projectId } = useParams()
  const user = useAuthStore((state) => state.user)
  const projectQuery = useProject(projectId)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const deleteProject = useDeleteProject(projectId ?? "")

  if (projectQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  if (projectQuery.isError || !projectQuery.data) {
    return (
      <ErrorPanel
        title="Could not load this project"
        message={getApiErrorMessage(projectQuery.error, "Project not found")}
      />
    )
  }

  const project = projectQuery.data
  const isOwner = user?.id === project.owner_id

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link
            to="/projects"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Projects
          </Link>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight">
            {project.name}
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            {project.description || "No description"}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            Owner {project.owner.full_name} · Updated{" "}
            {formatDateTime(project.updated_at)}
          </p>
        </div>
        {isOwner ? (
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={() => setEditOpen(true)}>
              Edit
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={() => setDeleteOpen(true)}
            >
              Delete
            </Button>
          </div>
        ) : null}
      </div>

      <MemberList project={project} canManage={isOwner} />

      <ProjectTaskSection projectId={project.id} members={project.members} />

      <ActivityFeed projectId={project.id} />

      <EditProjectDialog
        project={project}
        open={editOpen}
        onOpenChange={setEditOpen}
      />
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete project"
        description="This permanently deletes the project and its tasks."
        confirmLabel="Delete project"
        pending={deleteProject.isPending}
        onConfirm={() => deleteProject.mutate()}
      />
    </div>
  )
}
