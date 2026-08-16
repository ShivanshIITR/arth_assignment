import { useRef, useState } from "react"

import { EmptyState, ErrorPanel } from "@/components/QueryState"
import { Button } from "@/components/ui/button"
import { getApiErrorMessage } from "@/lib/apiError"
import type { Attachment } from "@/types/attachment"

import { downloadAttachment } from "./api"
import { useAttachments, useDeleteAttachment, useUploadAttachment } from "./hooks"

function formatSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function AttachmentList({
  taskId,
  currentUserId,
  isOwner,
}: {
  taskId: string
  currentUserId: string | undefined
  isOwner: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [progress, setProgress] = useState<number | null>(null)
  const attachments = useAttachments(taskId)
  const upload = useUploadAttachment(taskId)
  const remove = useDeleteAttachment(taskId)

  function onFile(file: File | undefined) {
    if (!file) {
      return
    }
    setProgress(0)
    upload.mutate(
      { file, onProgress: setProgress },
      {
        onSettled: () => {
          setProgress(null)
          if (inputRef.current) {
            inputRef.current.value = ""
          }
        },
      },
    )
  }

  return (
    <section className="space-y-3 rounded-xl border bg-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold">Attachments</h2>
        <div>
          <input
            ref={inputRef}
            type="file"
            className="sr-only"
            id="attachment-upload"
            aria-label="Upload file"
            onChange={(event) => onFile(event.target.files?.[0])}
          />
          <Button
            type="button"
            variant="outline"
            disabled={upload.isPending}
            onClick={() => inputRef.current?.click()}
          >
            {upload.isPending ? "Uploading…" : "Choose file"}
          </Button>
        </div>
      </div>

      {progress !== null ? (
        <div
          className="h-2 overflow-hidden rounded-full bg-muted"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress}
          aria-label="Upload progress"
        >
          <div
            className="h-full bg-primary transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      ) : null}

      {upload.isError ? (
        <p className="text-sm text-destructive">
          {getApiErrorMessage(upload.error, "Could not upload file")}
        </p>
      ) : null}

      {attachments.isError ? (
        <ErrorPanel
          title="Could not load attachments"
          message={getApiErrorMessage(attachments.error)}
          onRetry={() => void attachments.refetch()}
        />
      ) : null}

      {attachments.data && attachments.data.length === 0 ? (
        <EmptyState
          title="No attachments yet"
          description="Upload a spec, screenshot, or other supporting file."
        />
      ) : null}

      <ul className="space-y-2">
        {(attachments.data ?? []).map((attachment: Attachment) => {
          const canDelete =
            currentUserId === attachment.uploaded_by || isOwner
          return (
            <li
              key={attachment.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg border px-3 py-2 text-sm"
            >
              <div>
                <button
                  type="button"
                  className="font-medium hover:underline"
                  onClick={() => void downloadAttachment(attachment)}
                >
                  {attachment.original_filename}
                </button>
                <p className="text-xs text-muted-foreground">
                  {formatSize(attachment.size_bytes)} · {attachment.uploader.full_name}
                </p>
              </div>
              {canDelete ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={remove.isPending}
                  onClick={() => remove.mutate(attachment)}
                >
                  Delete
                </Button>
              ) : null}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
