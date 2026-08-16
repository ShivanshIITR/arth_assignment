import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios"

import { useAuthStore } from "@/features/auth/store"
import type { TokenResponse } from "@/types/user"

declare module "axios" {
  interface InternalAxiosRequestConfig {
    _retry?: boolean
  }
}

const AUTH_PUBLIC_PATHS = ["/auth/login", "/auth/register", "/auth/refresh"]

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api/v1",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
})

let refreshPromise: Promise<string> | null = null

function matchesPath(url: string | undefined, path: string): boolean {
  return Boolean(url?.includes(path))
}

function isAuthPublicRequest(url: string | undefined): boolean {
  return AUTH_PUBLIC_PATHS.some((path) => matchesPath(url, path))
}

function isRefreshRequest(url: string | undefined): boolean {
  return matchesPath(url, "/auth/refresh")
}

function redirectToLogin(): void {
  const path = window.location.pathname
  if (path === "/login" || path === "/register") {
    return
  }
  window.location.assign("/login")
}

function failAuth(): void {
  useAuthStore.getState().clear()
  refreshPromise = null
  redirectToLogin()
}

async function requestNewAccessToken(): Promise<string> {
  const { data } = await apiClient.post<TokenResponse>("/auth/refresh")
  useAuthStore.getState().setAccessToken(data.access_token)
  return data.access_token
}

function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = requestNewAccessToken().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

apiClient.interceptors.request.use((config) => {
  if (typeof FormData !== "undefined" && config.data instanceof FormData) {
    config.headers.delete("Content-Type")
  }
  const token = useAuthStore.getState().accessToken
  if (token && !isAuthPublicRequest(config.url)) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status
    const original = error.config as InternalAxiosRequestConfig | undefined

    if (status !== 401 || !original) {
      return Promise.reject(error)
    }

    if (isRefreshRequest(original.url) || isAuthPublicRequest(original.url)) {
      return Promise.reject(error)
    }

    if (original._retry) {
      failAuth()
      return Promise.reject(error)
    }

    original._retry = true

    try {
      const token = await refreshAccessToken()
      original.headers.Authorization = `Bearer ${token}`
      return apiClient(original)
    } catch {
      failAuth()
      return Promise.reject(error)
    }
  },
)

export function getInFlightRefresh(): Promise<string> | null {
  return refreshPromise
}

export function resetAuthRefreshState(): void {
  refreshPromise = null
}

export { refreshAccessToken }
