import { message } from 'antd'
import type { AxiosError } from 'axios'

/**
 * Unified API error handler.
 * Extracts detail message from AxiosError or falls back to the provided fallback string.
 */
export function handleApiError(error: unknown, fallback: string): void {
  const axiosErr = error as AxiosError<{ detail?: string }>
  if (axiosErr.isAxiosError) {
    message.error(axiosErr.response?.data?.detail ?? axiosErr.message)
  } else if (
    error !== null &&
    typeof error === 'object' &&
    'detail' in error &&
    typeof (error as { detail?: unknown }).detail === 'string'
  ) {
    message.error((error as { detail: string }).detail)
  } else if (error instanceof Error) {
    message.error(error.message)
  } else {
    message.error(fallback)
  }
}
