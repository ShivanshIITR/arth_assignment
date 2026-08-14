import { useState } from "react"

import { ConfirmDialog } from "@/components/ConfirmDialog"
import { Button } from "@/components/ui/button"
import { formatDate } from "@/lib/dates"
import { getApiErrorMessage } from "@/lib/apiError"
import type { Project, ProjectMember } from "@/types/project"

import { useRemoveProjectMember } from "../hooks"
import { AddMemberDialog } from "./AddMemberDialog"

export function MemberList({
  project,
  canManage,
}: {
  project: Project
  canManage: boolean
}) {
  const [addOpen, setAddOpen] = useState(false)
  const [memberToRemove, setMemberToRemove] = useState<ProjectMember | null>(
    null,
  )
  const removeMember = useRemoveProjectMember(project.id)

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Members</h2>
        {canManage ? (
          <Button type="button" size="sm" onClick={() => setAddOpen(true)}>
            Add member
          </Button>
        ) : null}
      </div>
      <ul className="divide-y rounded-xl border bg-card">
        {project.members.map((member) => {
          const isOwner = member.user_id === project.owner_id
          return (
            <li
              key={member.user_id}
              className="flex items-center justify-between gap-4 px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium">
                  {member.full_name}
                  {isOwner ? (
                    <span className="ml-2 text-xs font-normal text-muted-foreground">
                      Owner
                    </span>
                  ) : null}
                </p>
                <p className="text-xs text-muted-foreground">
                  {member.email} · joined {formatDate(member.joined_at)}
                </p>
              </div>
              {canManage && !isOwner ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setMemberToRemove(member)}
                >
                  Remove
                </Button>
              ) : null}
            </li>
          )
        })}
      </ul>
      {removeMember.isError ? (
        <p className="text-sm text-destructive">
          {getApiErrorMessage(removeMember.error, "Could not remove member")}
        </p>
      ) : null}

      <AddMemberDialog
        projectId={project.id}
        open={addOpen}
        onOpenChange={setAddOpen}
      />
      <ConfirmDialog
        open={Boolean(memberToRemove)}
        onOpenChange={(open) => {
          if (!open) {
            setMemberToRemove(null)
          }
        }}
        title="Remove member"
        description={
          memberToRemove
            ? `Remove ${memberToRemove.full_name} from this project?`
            : ""
        }
        confirmLabel="Remove"
        pending={removeMember.isPending}
        onConfirm={() => {
          if (!memberToRemove) {
            return
          }
          removeMember.mutate(memberToRemove.user_id, {
            onSuccess: () => setMemberToRemove(null),
          })
        }}
      />
    </section>
  )
}
