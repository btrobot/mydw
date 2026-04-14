import api from '@/services/api'

import type {
  AdminSessionResponse,
  AuthStatusResponse,
  LocalAuthSessionSummary,
} from './types'

export const AUTH_SESSION_QUERY_KEY = ['auth', 'session'] as const
export const AUTH_STATUS_QUERY_KEY = ['auth', 'status'] as const
export const AUTH_ADMIN_SESSIONS_QUERY_KEY = ['auth', 'admin', 'sessions'] as const

export interface AuthLoginRequest {
  username: string
  password: string
  device_id: string
  client_version: string
}

export interface AuthRefreshRequest {
  client_version: string
}

export const fetchAuthSession = async (): Promise<LocalAuthSessionSummary> => {
  const response = await api.get<LocalAuthSessionSummary>('/auth/session')
  return response.data
}

export const fetchAuthStatus = async (): Promise<AuthStatusResponse> => {
  const response = await api.get<AuthStatusResponse>('/auth/status')
  return response.data
}

export const fetchAdminSessions = async (): Promise<AdminSessionResponse[]> => {
  const response = await api.get<AdminSessionResponse[]>('/admin/sessions')
  return response.data
}

export const revokeAdminSession = async (
  sessionId: number
): Promise<{
  success: boolean
  revoked_session: AdminSessionResponse
  current_session: LocalAuthSessionSummary
}> => {
  const response = await api.post(`/admin/sessions/${sessionId}/revoke`)
  return response.data
}

export const loginAuth = async (payload: AuthLoginRequest): Promise<LocalAuthSessionSummary> => {
  const response = await api.post<LocalAuthSessionSummary>('/auth/login', payload)
  return response.data
}

export const refreshAuth = async (payload: AuthRefreshRequest): Promise<LocalAuthSessionSummary> => {
  const response = await api.post<LocalAuthSessionSummary>('/auth/refresh', payload)
  return response.data
}

export const logoutAuth = async (): Promise<LocalAuthSessionSummary> => {
  const response = await api.post<LocalAuthSessionSummary>('/auth/logout')
  return response.data
}

export const fetchAuthMe = async () => {
  const response = await api.get('/auth/me')
  return response.data
}
