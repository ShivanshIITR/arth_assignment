import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect } from "react"
import { useForm } from "react-hook-form"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { getApiErrorMessage } from "@/lib/apiError"
import type { Project } from "@/types/project"

import { useUpdateProject } from "../hooks"
import { projectFormSchema, type ProjectFormValues } from "../schemas"

export function EditProjectDialog({
  project,
  open,
  onOpenChange,
}: {
  project: Project
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const updateProject = useUpdateProject(project.id)
  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectFormSchema),
    defaultValues: {
      name: project.name,
      description: project.description ?? "",
    },
  })

  useEffect(() => {
    form.reset({
      name: project.name,
      description: project.description ?? "",
    })
  }, [form, project.description, project.name, open])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit project</DialogTitle>
          <DialogDescription>Update the name or description.</DialogDescription>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={form.handleSubmit((values) => {
            updateProject.mutate(
              {
                name: values.name.trim(),
                description: values.description?.trim() || null,
              },
              { onSuccess: () => onOpenChange(false) },
            )
          })}
        >
          <div className="space-y-2">
            <Label htmlFor="edit-project-name">Name</Label>
            <Input id="edit-project-name" {...form.register("name")} />
            {form.formState.errors.name ? (
              <p className="text-sm text-destructive">
                {form.formState.errors.name.message}
              </p>
            ) : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit-project-description">Description</Label>
            <Textarea
              id="edit-project-description"
              rows={4}
              {...form.register("description")}
            />
          </div>
          {updateProject.isError ? (
            <p className="text-sm text-destructive">
              {getApiErrorMessage(updateProject.error, "Could not update project")}
            </p>
          ) : null}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={updateProject.isPending}>
              {updateProject.isPending ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
