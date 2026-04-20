import type { AuthState, AuthStatusResponse, LocalAuthSessionSummary } from './types'

export interface AuthErrorDescriptor {
  title: string
  description: string
  severity: 'error' | 'warning' | 'info'
  retryLabel?: string
}

export interface AuthLoginCopy {
  title: string
  subtitle: string
  helper: string
  usernameLabel: string
  usernamePlaceholder: string
  usernameRequiredMessage: string
  passwordLabel: string
  passwordPlaceholder: string
  passwordRequiredMessage: string
  submitLabel: string
  retryLabel: string
  rememberMeLabel: string
  rememberMeHint: string
  statusSyncLoading: string
  statusSyncError: string
  statusSyncRetryLabel: string
  diagnosticsLabel: string
  diagnosticsDescription: string
  diagnosticsDeviceIdLabel: string
  diagnosticsClientVersionLabel: string
}

export interface AuthBootstrapCopy {
  loadingTitle: string
  loadingDescription: string
  loadingTip: string
  errorTitle: string
  errorDescription: string
  retryLabel: string
  retryingLabel: string
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

export const AUTH_LOGIN_COPY: AuthLoginCopy = {
  title: '登录创作控制台',
  subtitle: '继续使用作品工作台、任务管理和素材管理。',
  helper: '请输入账号和密码，继续进入当前工作区。',
  usernameLabel: '账号',
  usernamePlaceholder: '请输入账号',
  usernameRequiredMessage: '请输入账号',
  passwordLabel: '密码',
  passwordPlaceholder: '请输入密码',
  passwordRequiredMessage: '请输入密码',
  submitLabel: '登录',
  retryLabel: '重新提交',
  rememberMeLabel: '记住本次选择',
  rememberMeHint: '仅保留当前界面选择，不会改变设备绑定、会话有效期或后端登录策略。',
  statusSyncLoading: '正在检查当前登录状态，请稍候。',
  statusSyncError: '当前状态检查暂不可用，你仍可继续提交登录。',
  statusSyncRetryLabel: '重新检查',
  diagnosticsLabel: '登录环境信息',
  diagnosticsDescription: '以下信息仅用于排查当前登录环境问题，默认不会影响主流程阅读。',
  diagnosticsDeviceIdLabel: '设备标识',
  diagnosticsClientVersionLabel: '客户端版本',
}

export const AUTH_BOOTSTRAP_COPY: AuthBootstrapCopy = {
  loadingTitle: '正在准备登录环境',
  loadingDescription: '正在检查当前登录状态，请稍候。',
  loadingTip: '正在准备登录环境…',
  errorTitle: '暂时无法完成登录准备',
  errorDescription: '你仍可进入登录页继续尝试；如果问题持续，请稍后重新检查登录环境。',
  retryLabel: '重新检查',
  retryingLabel: '重新检查中…',
}

const STATE_MESSAGES: Record<AuthState, Omit<AuthErrorDescriptor, 'retryLabel'>> = {
  unauthenticated: {
    title: '请先登录',
    description: '登录后即可继续使用受保护的应用功能。',
    severity: 'info',
  },
  authorizing: {
    title: '正在验证登录信息',
    description: '应用正在建立当前登录会话，请稍候。',
    severity: 'info',
  },
  authenticated_active: {
    title: '已登录',
    description: '当前可以正常访问应用。',
    severity: 'info',
  },
  authenticated_grace: {
    title: '宽限模式',
    description: '当前授权服务暂不可用，你仍可查看已有内容，但受保护操作会受到限制。',
    severity: 'warning',
  },
  refresh_required: {
    title: '需要重新确认登录状态',
    description: '当前会话需要重新校验后才能继续，请重新登录或稍后重试。',
    severity: 'warning',
  },
  revoked: {
    title: '访问权限已失效',
    description: '当前账号的应用访问权限已失效，请联系管理员恢复后再登录。',
    severity: 'error',
  },
  device_mismatch: {
    title: '当前设备未通过校验',
    description: '请退出后重新登录；如果问题持续，请联系管理员重新绑定设备。',
    severity: 'error',
  },
  expired: {
    title: '登录已过期',
    description: '当前登录已过期，请重新登录后继续使用。',
    severity: 'warning',
  },
  error: {
    title: '授权服务暂不可用',
    description: '当前无法完成授权校验，请稍后重试；如果你刚刚提交过登录，请确认网络后再试一次。',
    severity: 'warning',
  },
}

const BACKEND_MESSAGES: Record<string, AuthErrorDescriptor> = {
  invalid_credentials: {
    title: '账号或密码错误',
    description: '请检查账号和密码后重新提交。',
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
  title: '登录请求未完成',
  description: '请稍后重试；如果问题持续存在，请重新登录或检查授权服务连接。',
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

  return FALLBACK_ERROR
}

export const getBootstrapErrorDescriptor = (_error: unknown): AuthErrorDescriptor => ({
  title: AUTH_BOOTSTRAP_COPY.errorTitle,
  description: AUTH_BOOTSTRAP_COPY.errorDescription,
  severity: 'warning',
  retryLabel: AUTH_BOOTSTRAP_COPY.retryLabel,
})
