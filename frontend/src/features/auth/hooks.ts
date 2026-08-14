import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"

import { queryKeys } from "@/lib/queryKeys"
import type { LoginRequest, RegisterRequest } from "@/types/user"

import { getCurrentUser, login, logout, register } from "./api"
import { useAuthStore } from "./store"

export function useLogin() {
  const navigate = useNavigate()
  const setSession = useAuthStore((state) => state.setSession)

  return useMutation({
    mutationFn: async (body: LoginRequest) => {
      const tokens = await login(body)
      useAuthStore.getState().setAccessToken(tokens.access_token)
      const user = await getCurrentUser()
      return { tokens, user }
    },
    onSuccess: ({ tokens, user }) => {
      setSession(tokens.access_token, user)
      void navigate("/", { replace: true })
    },
  })
}

export function useRegister() {
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (body: RegisterRequest) => register(body),
    onSuccess: () => {
      void navigate("/login", { replace: true, state: { registered: true } })
    },
  })
}

export function useLogout() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const clear = useAuthStore((state) => state.clear)

  return useMutation({
    mutationFn: logout,
    onSettled: () => {
      clear()
      queryClient.clear()
      void navigate("/login", { replace: true })
    },
  })
}

export function useCurrentUser() {
  const accessToken = useAuthStore((state) => state.accessToken)

  return useQuery({
    queryKey: queryKeys.me,
    queryFn: getCurrentUser,
    enabled: Boolean(accessToken),
  })
}
