import { useInfiniteQuery } from "@tanstack/react-query"

import { queryKeys } from "@/lib/queryKeys"

import { getProjectActivity } from "./api"

const PAGE_SIZE = 20

export function useProjectActivity(projectId: string | undefined) {
  return useInfiniteQuery({
    queryKey: queryKeys.projects.activity(projectId ?? ""),
    queryFn: ({ pageParam }) =>
      getProjectActivity(projectId!, pageParam, PAGE_SIZE),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.page * lastPage.page_size
      return loaded < lastPage.total ? lastPage.page + 1 : undefined
    },
    enabled: Boolean(projectId),
  })
}
