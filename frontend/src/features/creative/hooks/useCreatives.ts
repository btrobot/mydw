import { useQuery } from '@tanstack/react-query'

import {
  getCreativeApiCreativesCreativeIdGet,
  listCreativesApiCreativesGet,
} from '@/api'
import type {
  CreativeDetailResponse,
  CreativeWorkbenchListResponse,
} from '@/api'

export const useCreatives = (params?: { skip?: number; limit?: number }) =>
  useQuery<CreativeWorkbenchListResponse>({
    queryKey: ['creatives', params?.skip ?? 0, params?.limit ?? 50],
    queryFn: async () => {
      const response = await listCreativesApiCreativesGet({
        query: {
          skip: params?.skip ?? 0,
          limit: params?.limit ?? 50,
        },
      })

      return response.data ?? { total: 0, items: [] }
    },
  })

export const useCreative = (creativeId: number | undefined) =>
  useQuery<CreativeDetailResponse>({
    queryKey: ['creative', creativeId],
    queryFn: async () => {
      const response = await getCreativeApiCreativesCreativeIdGet({
        path: { creative_id: creativeId! },
      })

      return response.data!
    },
    enabled: creativeId !== undefined,
    retry: false,
  })
