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

export type AuthStatusVariant = 'revoked' | 'device_mismatch' | 'expired' | 'grace'

export interface AuthStatusTagMeta {
  color: string
  label: string
}

export interface AuthStatusPageCopy {
  descriptor: AuthErrorDescriptor
  loadingTitle: string
  loadingDescription: string
  refreshErrorTitle: string
  refreshErrorDescription: string
  diagnosticsLabel: string
  diagnosticsDescription: string
  emptyDiagnosticsText: string
  continueLabel?: string
  signoutLabel: string
}

export interface AuthRouteCopy {
  graceBannerTitle: string
  graceBannerDescription: string
}

export interface AuthHeaderCopy {
  logoutLabel: string
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

const AUTH_GRACE_DESCRIPTION = '当前授权服务暂不可用，你仍可查看已有内容，但受保护操作会受到限制。'
const AUTH_DIAGNOSTICS_TRIGGER_LABEL = '查看诊断信息'

export const AUTH_LOGIN_COPY: AuthLoginCopy = {
  title: '登录作品工作台',
  subtitle: '继续处理作品、审核与 AIClip 流程。',
  usernameLabel: '账号',
  usernamePlaceholder: '请输入账号',
  usernameRequiredMessage: '请输入账号',
  passwordLabel: '密码',
  passwordPlaceholder: '请输入密码',
  passwordRequiredMessage: '请输入密码',
  submitLabel: '登录并进入工作台',
  retryLabel: '重新提交',
  rememberMeLabel: '记住本次选择',
  rememberMeHint: '仅保留当前界面的记住选择，不会改变设备绑定或会话策略。',
  statusSyncLoading: '正在检查当前登录状态，请稍候。',
  statusSyncError: '当前状态检查暂不可用，你仍可继续提交登录。',
  statusSyncRetryLabel: '重新检查',
  diagnosticsLabel: AUTH_DIAGNOSTICS_TRIGGER_LABEL,
  diagnosticsDescription: '以下信息仅用于排查当前登录环境。',
  diagnosticsDeviceIdLabel: '设备标识',
  diagnosticsClientVersionLabel: '客户端版本',
}

export const AUTH_BOOTSTRAP_COPY: AuthBootstrapCopy = {
  loadingTitle: '正在准备登录环境',
  loadingDescription: '正在检查当前登录状态，请稍候。',
  loadingTip: '正在准备登录环境…',
  errorTitle: '暂时无法完成登录准备',
  errorDescription: '你仍可继续登录；如果问题持续，请稍后重新检查。',
  retryLabel: '重新检查',
  retryingLabel: '重新检查中…',
}

export const AUTH_ROUTE_COPY: AuthRouteCopy = {
  graceBannerTitle: '当前处于宽限模式',
  graceBannerDescription: AUTH_GRACE_DESCRIPTION,
}

export const AUTH_HEADER_COPY: AuthHeaderCopy = {
  logoutLabel: '退出登录',
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
    description: '当前可以继续处理作品、审核与常用业务流程。',
    severity: 'info',
  },
  authenticated_grace: {
    title: '宽限模式',
    description: AUTH_GRACE_DESCRIPTION,
    severity: 'warning',
  },
  refresh_required: {
    title: '需要重新确认登录状态',
    description: '当前会话需要重新确认，请重新登录后继续。',
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
    description: '当前无法完成授权校验，请稍后重试；如仍失败，请确认网络后重新登录。',
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

const AUTH_STATUS_TAG_META: Record<AuthState, AuthStatusTagMeta> = {
  authenticated_active: { color: 'success', label: '已登录' },
  authenticated_grace: { color: 'warning', label: '宽限模式' },
  revoked: { color: 'error', label: '权限失效' },
  device_mismatch: { color: 'error', label: '设备校验失败' },
  expired: { color: 'warning', label: '登录已过期' },
  refresh_required: { color: 'warning', label: '待重新确认' },
  authorizing: { color: 'processing', label: '校验中' },
  unauthenticated: { color: 'default', label: '未登录' },
  error: { color: 'warning', label: '状态异常' },
}

const AUTH_STATUS_PAGE_SHARED_COPY = {
  loadingTitle: '正在刷新授权状态',
  loadingDescription: '正在同步最新授权结果，请稍候。',
  refreshErrorTitle: '授权状态暂时无法刷新',
  refreshErrorDescription: '当前页面保留最近一次会话信息，请稍后再试。',
  diagnosticsLabel: AUTH_DIAGNOSTICS_TRIGGER_LABEL,
  diagnosticsDescription: '以下信息仅用于查看当前设备会话状态。',
  emptyDiagnosticsText: '暂无可展示的会话信息。',
  signoutLabel: '重新登录',
} satisfies Omit<AuthStatusPageCopy, 'descriptor' | 'continueLabel'>

const createHardStopStatusPageCopy = (descriptor: AuthErrorDescriptor): AuthStatusPageCopy => ({
  descriptor,
  ...AUTH_STATUS_PAGE_SHARED_COPY,
})

const AUTH_STATUS_PAGE_COPY: Record<AuthStatusVariant, AuthStatusPageCopy> = {
  revoked: createHardStopStatusPageCopy(STATE_MESSAGES.revoked),
  device_mismatch: createHardStopStatusPageCopy(STATE_MESSAGES.device_mismatch),
  expired: createHardStopStatusPageCopy(STATE_MESSAGES.expired),
  grace: {
    ...AUTH_STATUS_PAGE_SHARED_COPY,
    descriptor: {
      ...STATE_MESSAGES.authenticated_grace,
      severity: 'info',
    },
    continueLabel: '进入作品工作台',
    signoutLabel: '退出登录',
  },
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

export const getAuthStatusTagMeta = (
  authState: AuthState | 'unknown'
): AuthStatusTagMeta => (
  authState === 'unknown'
    ? { color: 'default', label: '状态未知' }
    : AUTH_STATUS_TAG_META[authState]
)

export const getAuthStatusPageCopy = (variant: AuthStatusVariant): AuthStatusPageCopy =>
  AUTH_STATUS_PAGE_COPY[variant]
