import type { QueryClient } from '@tanstack/react-query'

import { client } from '@/api/client.gen'
import api from '@/services/api'

import { AUTH_SESSION_QUERY_KEY, fetchAuthSession } from './api'
import type { LocalAuthSessionSummary } from './types'

const isAuthApiRequest = (url?: string) => Boolean(url && url.includes('/api/auth/'))
let authSessionSyncHook: (() => Promise<LocalAuthSessionSummary | null>) | null = null

export const syncAuthSessionFromBackend = async () =>
  authSessionSyncHook ? authSessionSyncHook() : null

export const installAuthTransportSync = (
  queryClient: QueryClient,
  setSession: (session: LocalAuthSessionSummary | null) => void
) => {
  const syncSession = async () => {
    try {
      const session = await fetchAuthSession()
      queryClient.setQueryData(AUTH_SESSION_QUERY_KEY, session)
      setSession(session ?? null)
      return session ?? null
    } catch {
      queryClient.setQueryData(AUTH_SESSION_QUERY_KEY, null)
      setSession(null)
      return null
    }
  }

  authSessionSyncHook = syncSession

  const axiosInterceptorId = api.interceptors.response.use(
    (response) => response,
    async (error) => {
      const status = error?.response?.status
      const url = error?.config?.url as string | undefined
      if ((status === 401 || status === 403) && !isAuthApiRequest(url)) {
        await syncSession()
      }
      return Promise.reject(error)
    }
  )

  const generatedClientInterceptorId = client.interceptors.response.use(async (response) => {
    if ((response.status === 401 || response.status === 403) && !isAuthApiRequest(response.url)) {
      await syncSession()
    }
    return response
  })

  return () => {
    if (authSessionSyncHook === syncSession) {
      authSessionSyncHook = null
    }
    api.interceptors.response.eject(axiosInterceptorId)
    client.interceptors.response.eject(generatedClientInterceptorId)
  }
}
