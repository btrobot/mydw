import { useQuery } from '@tanstack/react-query'

import { AUTH_STATUS_QUERY_KEY, fetchAuthStatus } from './api'

export const useAuthStatus = (enabled = true) =>
  useQuery({
    queryKey: AUTH_STATUS_QUERY_KEY,
    queryFn: fetchAuthStatus,
    enabled,
    retry: 0,
    staleTime: 0,
    refetchOnWindowFocus: false,
  })
