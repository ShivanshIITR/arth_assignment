import { apiClient } from "@/lib/apiClient"
import type { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types/user"

export async function login(body: LoginRequest): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", body)
  return data
}

export async function register(body: RegisterRequest): Promise<User> {
  const { data } = await apiClient.post<User>("/auth/register", body)
  return data
}

export async function refreshSession(): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/refresh")
  return data
}

export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout")
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me")
  return data
}
