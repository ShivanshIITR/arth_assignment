import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { Link, useParams } from "react-router-dom"

import { ConfirmDialog } from "@/components/ConfirmDialog"
import { ErrorPanel } from "@/components/QueryState"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { AttachmentList } from "@/features/attachments/AttachmentList"
import { useAuthStore } from "@/features/auth/store"
import { useProject } from "@/features/projects/hooks"
import { getApiErrorMessage } from "@/lib/apiError"
import { formatDateTime } from "@/lib/dates"
import { TASK_PRIORITIES } from "@/types/task"

import { PriorityBadge } from "./components/StatusBadge"
import { StatusSelect } from "./components/StatusSelect"
import {
  useDeleteTask,
  useTask,
  useTaskLiveUpdates,
  useUpdateTask,
  useUpdateTaskStatus,
} from "./hooks"
import {
  canCompleteTask,
  emptyToNull,
  taskFormSchema,
  type TaskFormValues,
} from "./schemas"

export function TaskDetailsPage() {
  const { projectId, taskId } = useParams()
  const user = useAuthStore((state) => state.user)
  const taskQuery = useTask(taskId)
  const projectQuery = useProject(projectId)
  useTaskLiveUpdates(projectId)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const updateTask = useUpdateTask(projectId ?? "", taskId ?? "")
  const updateStatus = useUpdateTaskStatus(projectId ?? "")
  const deleteTask = useDeleteTask(projectId ?? "", taskId ?? "")

  const form = useForm<TaskFormValues>({
    resolver: zodResolver(taskFormSchema),
    defaultValues: {
      title: "",
      description: "",
      status: "todo",
      priority: "medium",
      assignee_id: "",
      due_date: "",
    },
  })

  useEffect(() => {
    const task = taskQuery.data
    if (!task) {
      return
    }
    form.reset({
      title: task.title,
      description: task.description ?? "",
      status: task.status,
      priority: task.priority,
      assignee_id: task.assignee_id ?? "",
      due_date: task.due_date ?? "",
    })
  }, [form, taskQuery.data])

  if (taskQuery.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    )
  }

  if (taskQuery.isError || !taskQuery.data) {
    return (
      <ErrorPanel
        title="Could not load this task"
        message={getApiErrorMessage(taskQuery.error, "Task not found")}
      />
    )
  }

  const task = taskQuery.data
  const project = projectQuery.data
  const isOwner = Boolean(user && project && user.id === project.owner_id)
  const canEdit = Boolean(
    user &&
      (isOwner ||
        user.id === task.creator_id ||
        user.id === task.assignee_id),
  )
  const canDelete = isOwner && task.status === "todo"
  const members = project?.members ?? []

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <Link
          to={`/projects/${task.project_id}`}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          ← {project?.name ?? "Project"}
        </Link>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight">{task.title}</h1>
          <PriorityBadge priority={task.priority} />
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Created by {task.creator?.full_name ?? "Unknown"} ·{" "}
          {formatDateTime(task.created_at)}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <StatusSelect
          value={task.status}
          disabled={!canEdit || updateStatus.isPending}
          onChange={(status) =>
            updateStatus.mutate({ taskId: task.id, status })
          }
        />
        {!canCompleteTask(task) ? (
          <p className="text-xs text-muted-foreground">
            Completing a task requires an assignee and a due date.
          </p>
        ) : null}
      </div>
      {updateStatus.isError ? (
        <p className="text-sm text-destructive">
          {getApiErrorMessage(updateStatus.error, "Could not change status")}
        </p>
      ) : null}

      <form
        className="space-y-4 rounded-xl border bg-card p-5"
        onSubmit={form.handleSubmit((values) => {
          updateTask.mutate({
            title: values.title.trim(),
            description: emptyToNull(values.description),
            priority: values.priority,
            assignee_id: emptyToNull(values.assignee_id),
            due_date: emptyToNull(values.due_date),
          })
        })}
      >
        <div className="space-y-2">
          <Label htmlFor="edit-title">Title</Label>
          <Input id="edit-title" disabled={!canEdit} {...form.register("title")} />
          {form.formState.errors.title ? (
            <p className="text-sm text-destructive">
              {form.formState.errors.title.message}
            </p>
          ) : null}
        </div>
        <div className="space-y-2">
          <Label htmlFor="edit-description">Description</Label>
          <Textarea
            id="edit-description"
            rows={5}
            disabled={!canEdit}
            {...form.register("description")}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Priority</Label>
            <Select
              value={form.watch("priority")}
              disabled={!canEdit}
              onValueChange={(value) =>
                form.setValue("priority", value as TaskFormValues["priority"])
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TASK_PRIORITIES.map((priority) => (
                  <SelectItem key={priority} value={priority}>
                    {priority}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-due-date">Due date</Label>
            <Input
              id="edit-due-date"
              type="date"
              disabled={!canEdit}
              {...form.register("due_date")}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label>Assignee</Label>
          <Select
            value={form.watch("assignee_id") || "unassigned"}
            disabled={!canEdit}
            onValueChange={(value) =>
              form.setValue("assignee_id", value === "unassigned" ? "" : value)
            }
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="unassigned">Unassigned</SelectItem>
              {members.map((member) => (
                <SelectItem key={member.user_id} value={member.user_id}>
                  {member.full_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {updateTask.isError ? (
          <p className="text-sm text-destructive">
            {getApiErrorMessage(updateTask.error, "Could not update task")}
          </p>
        ) : null}
        {canEdit ? (
          <Button type="submit" disabled={updateTask.isPending}>
            {updateTask.isPending ? "Saving…" : "Save changes"}
          </Button>
        ) : (
          <p className="text-sm text-muted-foreground">
            Only the project owner, creator, or assignee can edit this task.
          </p>
        )}
      </form>

      <AttachmentList
        taskId={task.id}
        currentUserId={user?.id}
        isOwner={isOwner}
      />

      {canDelete ? (
        <div>
          <Button
            type="button"
            variant="destructive"
            onClick={() => setDeleteOpen(true)}
          >
            Delete task
          </Button>
        </div>
      ) : null}

      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete task"
        description="Only to-do tasks can be deleted, and only by the project owner."
        confirmLabel="Delete task"
        pending={deleteTask.isPending}
        onConfirm={() => deleteTask.mutate()}
      />
    </div>
  )
}
