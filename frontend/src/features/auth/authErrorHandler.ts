import type { AuthState, AuthStatusResponse, LocalAuthSessionSummary } from './types'

export interface AuthErrorDescriptor {
  title: string
  description: string
  severity: 'error' | 'warning' | 'info'
  retryLabel?: string
}

type BackendErrorLike = {
  response?: {
    data?: {
      detail?: {
        error_code?: string
        message?: string
      }
    }
  }
  message?: string
}

const STATE_MESSAGES: Record<
  AuthState,
  Omit<AuthErrorDescriptor, 'retryLabel'>
> = {
  unauthenticated: {
    title: 'Sign in required',
    description: 'Please sign in to continue using protected local features.',
    severity: 'info',
  },
  authorizing: {
    title: 'Authorization in progress',
    description: 'The app is still establishing your local authorization session.',
    severity: 'info',
  },
  authenticated_active: {
    title: 'Authorized',
    description: 'Your local authorization session is active.',
    severity: 'info',
  },
  authenticated_grace: {
    title: 'Offline grace mode',
    description: 'You can view existing local data, but high-risk actions stay blocked until the authorization service is reachable again.',
    severity: 'warning',
  },
  refresh_required: {
    title: 'Session refresh required',
    description: 'Your session needs to refresh before protected actions can continue.',
    severity: 'warning',
  },
  revoked: {
    title: 'Authorization revoked',
    description: 'The remote authorization has been revoked or disabled. Please sign in again to continue.',
    severity: 'error',
  },
  device_mismatch: {
    title: 'Device authorization mismatch',
    description: 'This device no longer matches the remote authorization record. Please sign in again or re-bind this device.',
    severity: 'error',
  },
  expired: {
    title: 'Session expired',
    description: 'Your local authorization session has expired. Please sign in again.',
    severity: 'warning',
  },
  error: {
    title: 'Authorization unavailable',
    description: 'The authorization service is unavailable right now. Please try again.',
    severity: 'warning',
  },
}

const BACKEND_MESSAGES: Record<string, AuthErrorDescriptor> = {
  invalid_credentials: {
    title: 'Incorrect username or password',
    description: 'Double-check your credentials and try signing in again.',
    severity: 'error',
  },
  network_timeout: {
    title: 'Authorization service unavailable',
    description: 'We could not reach the authorization service. Check your network connection and try again.',
    severity: 'warning',
    retryLabel: 'Retry',
  },
  transport_error: {
    title: 'Authorization service unavailable',
    description: 'We could not reach the authorization service. Check your network connection and try again.',
    severity: 'warning',
    retryLabel: 'Retry',
  },
  revoked: STATE_MESSAGES.revoked,
  device_mismatch: STATE_MESSAGES.device_mismatch,
  expired: STATE_MESSAGES.expired,
}

const FALLBACK_ERROR: AuthErrorDescriptor = {
  title: 'Authorization request failed',
  description: 'Please try again. If the problem continues, sign in again or reconnect to the authorization service.',
  severity: 'warning',
  retryLabel: 'Retry',
}

export const getAuthStateDescriptor = (
  input?: Pick<LocalAuthSessionSummary, 'auth_state' | 'denial_reason'> | Pick<AuthStatusResponse, 'auth_state' | 'denial_reason'> | null
): AuthErrorDescriptor | null => {
  if (!input?.auth_state) {
    return null
  }

  const descriptor = STATE_MESSAGES[input.auth_state]
  if (!descriptor) {
    return null
  }

  const denialHint =
    input.denial_reason && !['revoked', 'device_mismatch'].includes(input.denial_reason)
      ? ` Reason: ${input.denial_reason}.`
      : ''

  return {
    ...descriptor,
    description: `${descriptor.description}${denialHint}`,
  }
}

export const getAuthErrorDescriptor = (error: unknown): AuthErrorDescriptor => {
  const backendError = error as BackendErrorLike | undefined
  const detail = backendError?.response?.data?.detail
  const descriptor = detail?.error_code ? BACKEND_MESSAGES[detail.error_code] : undefined

  if (descriptor) {
    return descriptor
  }

  if (error instanceof Error) {
    return {
      ...FALLBACK_ERROR,
      description: error.message || FALLBACK_ERROR.description,
    }
  }

  return FALLBACK_ERROR
}
