import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { handleMutationError, toastSuccess } from "@/lib/feedback"
import { queryKeys } from "@/lib/queryKeys"
import type { Attachment } from "@/types/attachment"

import {
  deleteAttachment,
  listAttachments,
  uploadAttachment,
} from "./api"

export function useAttachments(taskId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.tasks.attachments(taskId ?? ""),
    queryFn: () => listAttachments(taskId!),
    enabled: Boolean(taskId),
  })
}

export function useUploadAttachment(taskId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      file,
      onProgress,
    }: {
      file: File
      onProgress?: (percent: number) => void
    }) => uploadAttachment(taskId, file, onProgress),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.tasks.attachments(taskId),
      })
      toastSuccess("Attachment uploaded")
    },
    onError: (error) =>
      handleMutationError(error, {
        fallback: "Could not upload file",
        invalidateQueryKey: queryKeys.tasks.attachments(taskId),
      }),
  })
}

export function useDeleteAttachment(taskId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (attachment: Attachment) => deleteAttachment(attachment.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.tasks.attachments(taskId),
      })
      toastSuccess("Attachment deleted")
    },
    onError: (error) =>
      handleMutationError(error, {
        fallback: "Could not delete attachment",
        invalidateQueryKey: queryKeys.tasks.attachments(taskId),
      }),
  })
}
