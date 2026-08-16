import type { User } from "@/types/user"

export type Attachment = {
  id: string
  task_id: string
  uploaded_by: string
  uploader: User
  original_filename: string
  content_type: string
  size_bytes: number
  created_at: string
}

export type AttachmentListResponse = {
  items: Attachment[]
}
