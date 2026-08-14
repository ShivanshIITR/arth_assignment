import { create } from "zustand"

import type { User } from "@/types/user"

type AuthState = {
  accessToken: string | null
  user: User | null
  setAccessToken: (accessToken: string) => void
  setUser: (user: User | null) => void
  setSession: (accessToken: string, user: User | null) => void
  clear: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  setAccessToken: (accessToken) => set({ accessToken }),
  setUser: (user) => set({ user }),
  setSession: (accessToken, user) => set({ accessToken, user }),
  clear: () => set({ accessToken: null, user: null }),
}))
