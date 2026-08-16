import { apiClient } from "@/lib/apiClient"
import type { ActivityPage } from "@/types/activity"

export async function getProjectActivity(
  projectId: string,
  page = 1,
  pageSize = 20,
): Promise<ActivityPage> {
  const { data } = await apiClient.get<ActivityPage>(
    `/projects/${projectId}/activity`,
    { params: { page, page_size: pageSize } },
  )
  return data
}
