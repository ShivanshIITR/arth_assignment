export const queryKeys = {
  me: ["auth", "me"] as const,
  projects: {
    all: ["projects"] as const,
    list: (page: number, pageSize: number) =>
      ["projects", { page, pageSize }] as const,
    detail: (id: string) => ["projects", id] as const,
    tasks: (projectId: string, filters: Record<string, unknown>) =>
      ["projects", projectId, "tasks", filters] as const,
    activity: (id: string) => ["projects", id, "activity"] as const,
  },
  tasks: {
    detail: (id: string) => ["tasks", id] as const,
  },
  dashboard: {
    stats: ["dashboard", "stats"] as const,
  },
}
