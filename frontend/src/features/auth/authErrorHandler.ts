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
    title: '已登录',
    description: '当前可正常访问应用。',
    severity: 'info',
  },
  authenticated_grace: {
    title: '宽限模式',
    description: '当前网络或授权服务暂不可用，你仍可查看已有内容，但受保护操作会受限。',
    severity: 'warning',
  },
  refresh_required: {
    title: '需要重新确认登录状态',
    description: '当前会话需要刷新后才能继续，请重新登录或稍后重试。',
    severity: 'warning',
  },
  revoked: {
    title: '访问权限已失效',
    description: '当前账号的应用访问权限已失效，请联系管理员恢复权限后再登录。',
    severity: 'error',
  },
  device_mismatch: {
    title: '当前设备未通过校验',
    description: '请退出后重新登录；若问题持续，请联系管理员重新绑定设备。',
    severity: 'error',
  },
  expired: {
    title: '登录已过期',
    description: '当前登录已过期，请重新登录继续使用。',
    severity: 'warning',
  },
  error: {
    title: '授权服务暂不可用',
    description: '当前无法完成授权校验，请稍后重试；若你刚刚提交过登录，请确认网络后再次尝试。',
    severity: 'warning',
  },
}

const BACKEND_MESSAGES: Record<string, AuthErrorDescriptor> = {
  invalid_credentials: {
    title: '账号或密码错误',
    description: '请检查用户名和密码后重新提交。',
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
