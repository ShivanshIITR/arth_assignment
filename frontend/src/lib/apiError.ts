import type { AxiosError } from "axios"
import axios from "axios"

export type ApiErrorEnvelope = {
  error: {
    code: string
    message: string
    details?: unknown
  }
}

export function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (typeof value !== "object" || value === null || !("error" in value)) {
    return false
  }
  const error = (value as { error: unknown }).error
  if (typeof error !== "object" || error === null) {
    return false
  }
  const body = error as { code?: unknown; message?: unknown }
  return typeof body.code === "string" && typeof body.message === "string"
}

export function getApiErrorMessage(
  error: unknown,
  fallback = "Something went wrong",
): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data
    if (isApiErrorEnvelope(data)) {
      return data.error.message
    }
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}

export function getApiErrorCode(error: unknown): string | undefined {
  if (!axios.isAxiosError(error)) {
    return undefined
  }
  const data = error.response?.data
  if (isApiErrorEnvelope(data)) {
    return data.error.code
  }
  return undefined
}

export function getHttpStatus(error: unknown): number | undefined {
  if (axios.isAxiosError(error)) {
    return error.response?.status
  }
  return undefined
}

export function isForbiddenError(error: unknown): boolean {
  return getHttpStatus(error) === 403
}

export function isUnauthorizedError(error: unknown): boolean {
  return getHttpStatus(error) === 401
}

export type AppAxiosError = AxiosError<ApiErrorEnvelope>
