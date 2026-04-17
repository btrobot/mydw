import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  approveCreativeApiCreativeReviewsCreativeIdApprovePost,
  getCreativeApiCreativesCreativeIdGet,
  listCreativesApiCreativesGet,
  rejectCreativeApiCreativeReviewsCreativeIdRejectPost,
  reworkCreativeApiCreativeReviewsCreativeIdReworkPost,
} from '@/api'
import type {
  CreativeApproveRequest,
  CreativeDetailResponse,
  CreativeRejectRequest,
  CreativeReviewActionResponse,
  CreativeReworkRequest,
  CreativeWorkbenchListResponse,
} from '@/api'

export const creativeQueryKeys = {
  all: ['creatives'] as const,
  lists: () => [...creativeQueryKeys.all, 'list'] as const,
  list: (params?: { skip?: number; limit?: number }) =>
    [...creativeQueryKeys.lists(), params?.skip ?? 0, params?.limit ?? 50] as const,
  details: () => [...creativeQueryKeys.all, 'detail'] as const,
  detail: (creativeId: number | undefined) => [...creativeQueryKeys.details(), creativeId] as const,
}

export const useCreatives = (params?: { skip?: number; limit?: number }) =>
  useQuery<CreativeWorkbenchListResponse>({
    queryKey: creativeQueryKeys.list(params),
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
    queryKey: creativeQueryKeys.detail(creativeId),
    queryFn: async () => {
      const response = await getCreativeApiCreativesCreativeIdGet({
        path: { creative_id: creativeId! },
      })

      return response.data!
    },
    enabled: creativeId !== undefined,
    retry: false,
  })

const invalidateCreativeQueries = async (
  queryClient: ReturnType<typeof useQueryClient>,
  creativeId: number,
) => {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: creativeQueryKeys.detail(creativeId) }),
    queryClient.invalidateQueries({ queryKey: creativeQueryKeys.lists() }),
  ])
}

export const useApproveCreative = (creativeId: number | undefined) => {
  const queryClient = useQueryClient()

  return useMutation<CreativeReviewActionResponse | undefined, Error, CreativeApproveRequest>({
    mutationFn: async (body) => {
      const response = await approveCreativeApiCreativeReviewsCreativeIdApprovePost({
        path: { creative_id: creativeId! },
        body,
      })

      return response.data
    },
    onSuccess: async () => {
      if (creativeId !== undefined) {
        await invalidateCreativeQueries(queryClient, creativeId)
      }
    },
  })
}

export const useReworkCreative = (creativeId: number | undefined) => {
  const queryClient = useQueryClient()

  return useMutation<CreativeReviewActionResponse | undefined, Error, CreativeReworkRequest>({
    mutationFn: async (body) => {
      const response = await reworkCreativeApiCreativeReviewsCreativeIdReworkPost({
        path: { creative_id: creativeId! },
        body,
      })

      return response.data
    },
    onSuccess: async () => {
      if (creativeId !== undefined) {
        await invalidateCreativeQueries(queryClient, creativeId)
      }
    },
  })
}

export const useRejectCreative = (creativeId: number | undefined) => {
  const queryClient = useQueryClient()

  return useMutation<CreativeReviewActionResponse | undefined, Error, CreativeRejectRequest>({
    mutationFn: async (body) => {
      const response = await rejectCreativeApiCreativeReviewsCreativeIdRejectPost({
        path: { creative_id: creativeId! },
        body,
      })

      return response.data
    },
    onSuccess: async () => {
      if (creativeId !== undefined) {
        await invalidateCreativeQueries(queryClient, creativeId)
      }
    },
  })
}
