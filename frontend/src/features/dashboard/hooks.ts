import { useQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"

import { getDashboardStats } from "./api"

export function useDashboardStats() {
  return useQuery({
    queryKey: queryKeys.dashboard.stats,
    queryFn: getDashboardStats,
  })
}
