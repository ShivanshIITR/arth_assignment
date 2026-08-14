import { toast } from "sonner"

import { getApiErrorMessage, isForbiddenError } from "./apiError"
import { queryClient } from "./queryClient"

export function toastSuccess(message: string): void {
  toast.success(message)
}

export function toastApiError(error: unknown, fallback?: string): void {
  toast.error(getApiErrorMessage(error, fallback))
}

export function handleMutationError(
  error: unknown,
  options?: {
    fallback?: string
    invalidateQueryKey?: readonly unknown[]
  },
): void {
  toastApiError(error, options?.fallback)
  if (isForbiddenError(error) && options?.invalidateQueryKey) {
    void queryClient.invalidateQueries({ queryKey: [...options.invalidateQueryKey] })
  }
}
