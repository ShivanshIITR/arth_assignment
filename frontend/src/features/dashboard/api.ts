import { apiClient } from "@/lib/apiClient"
import type { DashboardStats } from "@/types/task"

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>("/dashboard/stats")
  return data
}
