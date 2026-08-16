import { apiClient } from "@/lib/apiClient"
import type { Attachment, AttachmentListResponse } from "@/types/attachment"

export async function listAttachments(taskId: string): Promise<Attachment[]> {
  const { data } = await apiClient.get<AttachmentListResponse>(
    `/tasks/${taskId}/attachments`,
  )
  return data.items
}

export async function uploadAttachment(
  taskId: string,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<Attachment> {
  const body = new FormData()
  body.append("file", file)
  const { data } = await apiClient.post<Attachment>(
    `/tasks/${taskId}/attachments`,
    body,
    {
      onUploadProgress: (event) => {
        if (event.total) {
          onProgress?.(Math.round((event.loaded / event.total) * 100))
        }
      },
    },
  )
  return data
}

export async function downloadAttachment(
  attachment: Attachment,
): Promise<void> {
  const { data } = await apiClient.get<Blob>(
    `/attachments/${attachment.id}/download`,
    { responseType: "blob" },
  )
  const url = URL.createObjectURL(data)
  const link = document.createElement("a")
  link.href = url
  link.download = attachment.original_filename
  link.click()
  URL.revokeObjectURL(url)
}

export async function deleteAttachment(attachmentId: string): Promise<void> {
  await apiClient.delete(`/attachments/${attachmentId}`)
}
