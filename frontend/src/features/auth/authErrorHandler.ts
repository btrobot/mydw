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
    title: '请先登录',
    description: '登录后才能继续使用受保护的本地功能。',
    severity: 'info',
  },
  authorizing: {
    title: '正在校验授权',
    description: '应用正在建立本地授权会话，请稍候。',
    severity: 'info',
  },
  authenticated_active: {
    title: '授权有效',
    description: '当前本地授权会话可正常使用。',
    severity: 'info',
  },
  authenticated_grace: {
    title: '离线宽限模式',
    description: '你仍可查看现有本地数据，但高风险操作会继续受限，直到授权服务恢复可用。',
    severity: 'warning',
  },
  refresh_required: {
    title: '需要刷新会话',
    description: '继续执行受保护操作前，需要先刷新当前授权会话。',
    severity: 'warning',
  },
  revoked: {
    title: '授权已失效',
    description: '远端授权已被撤销或停用，请重新登录后继续使用。',
    severity: 'error',
  },
  device_mismatch: {
    title: '设备授权不匹配',
    description: '当前设备与远端授权记录不一致，请重新登录或重新绑定设备。',
    severity: 'error',
  },
  expired: {
    title: '登录已过期',
    description: '当前本地授权会话已过期，请重新登录。',
    severity: 'warning',
  },
  error: {
    title: '授权服务暂不可用',
    description: '当前无法连接授权服务，请稍后重试。',
    severity: 'warning',
  },
}

const BACKEND_MESSAGES: Record<string, AuthErrorDescriptor> = {
  invalid_credentials: {
    title: '账号或密码错误',
    description: '请检查登录信息后重试。',
    severity: 'error',
  },
  network_timeout: {
    title: '授权服务暂不可用',
    description: '暂时无法连接授权服务，请检查网络后重试。',
    severity: 'warning',
    retryLabel: '重试',
  },
  transport_error: {
    title: '授权服务暂不可用',
    description: '暂时无法连接授权服务，请检查网络后重试。',
    severity: 'warning',
    retryLabel: '重试',
  },
  revoked: STATE_MESSAGES.revoked,
  device_mismatch: STATE_MESSAGES.device_mismatch,
  expired: STATE_MESSAGES.expired,
}

const FALLBACK_ERROR: AuthErrorDescriptor = {
  title: '授权请求失败',
  description: '请稍后重试。如果问题持续存在，请重新登录或检查授权服务连接。',
  severity: 'warning',
  retryLabel: '重试',
}

const DENIAL_REASON_HINTS: Record<string, string> = {
  network_timeout: '当前授权服务连接超时，请稍后重试。',
  transport_error: '当前授权服务连接异常，请稍后重试。',
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
      ? ` ${DENIAL_REASON_HINTS[input.denial_reason] ?? '当前授权状态需要重新校验，请稍后重试。'}`
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
