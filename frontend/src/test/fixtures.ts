import type { Attachment } from "@/types/attachment"
import type { DashboardStats } from "@/types/task"
import type { Project } from "@/types/project"
import type { Task } from "@/types/task"
import type { User } from "@/types/user"

export const userFixture: User = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "owner@example.com",
  full_name: "Owner User",
  created_at: "2026-01-01T00:00:00Z",
}

export const memberFixture: User = {
  id: "22222222-2222-2222-2222-222222222222",
  email: "member@example.com",
  full_name: "Member User",
  created_at: "2026-01-01T00:00:00Z",
}

export const projectFixture: Project = {
  id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  name: "Website launch",
  description: "Ship the marketing site",
  owner_id: userFixture.id,
  owner: userFixture,
  members: [
    {
      user_id: userFixture.id,
      email: userFixture.email,
      full_name: userFixture.full_name,
      joined_at: "2026-01-02T00:00:00Z",
    },
  ],
  created_at: "2026-01-02T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
}

export const taskFixture: Task = {
  id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
  project_id: projectFixture.id,
  title: "Write copy",
  description: "Homepage hero",
  status: "todo",
  priority: "high",
  assignee_id: userFixture.id,
  creator_id: userFixture.id,
  due_date: "2026-02-01",
  assignee: userFixture,
  creator: userFixture,
  created_at: "2026-01-03T00:00:00Z",
  updated_at: "2026-01-03T00:00:00Z",
}

export const dashboardFixture: DashboardStats = {
  total_projects: 1,
  active_projects: 1,
  total_tasks: 1,
  completed_tasks: 0,
  pending_tasks: 1,
  tasks_by_status: { todo: 1, in_progress: 0, completed: 0 },
}

export const attachmentFixture: Attachment = {
  id: "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
  task_id: taskFixture.id,
  uploaded_by: memberFixture.id,
  uploader: memberFixture,
  original_filename: "spec.txt",
  content_type: "text/plain",
  size_bytes: 12,
  created_at: "2026-01-04T00:00:00Z",
}

export const tokenFixture = {
  access_token: "access-token",
  token_type: "bearer",
  expires_in: 900,
}
