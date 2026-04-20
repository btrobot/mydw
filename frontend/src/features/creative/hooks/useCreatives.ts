import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  approveCreativeApiCreativeReviewsCreativeIdApprovePost,
  createCreativeApiCreativesPost,
  getCreativeApiCreativesCreativeIdGet,
  getPublishStatusApiPublishStatusGet,
  getScheduleConfigApiScheduleConfigGet,
  listCreativesApiCreativesGet,
  listPublishPoolItemsApiCreativePublishPoolGet,
  rejectCreativeApiCreativeReviewsCreativeIdRejectPost,
  reworkCreativeApiCreativeReviewsCreativeIdReworkPost,
  submitCreativeCompositionApiCreativesCreativeIdSubmitCompositionPost,
  updateCreativeApiCreativesCreativeIdPatch,
} from '@/api'
import type {
  CreativeApproveRequest,
  CreativeComposeSubmitResponse,
  CreativeCreateRequest,
  CreativeDetailResponse,
  CreativeRejectRequest,
  CreativeReviewActionResponse,
  CreativeReworkRequest,
  CreativeUpdateRequest,
  CreativeWorkbenchListResponse,
  PublishPoolListResponse,
  PublishPoolStatus,
  PublishStatusResponse,
  ScheduleConfigResponse,
} from '@/api'

export type CreativeListParams = {
  skip?: number
  limit?: number
  enabled?: boolean
}

export const creativeQueryKeys = {
  all: ['creatives'] as const,
  lists: () => [...creativeQueryKeys.all, 'list'] as const,
  list: (params?: CreativeListParams) =>
    [...creativeQueryKeys.lists(), params?.skip ?? 0, params?.limit ?? 50] as const,
  details: () => [...creativeQueryKeys.all, 'detail'] as const,
  detail: (creativeId: number | undefined) => [...creativeQueryKeys.details(), creativeId] as const,
  publishPool: () => [...creativeQueryKeys.all, 'publish-pool'] as const,
  publishPoolList: (params?: {
    skip?: number
    limit?: number
    status?: PublishPoolStatus
    creativeId?: number
  }) =>
    [
      ...creativeQueryKeys.publishPool(),
      params?.skip ?? 0,
      params?.limit ?? 50,
      params?.status ?? 'active',
      params?.creativeId ?? 'all',
    ] as const,
  publishStatus: () => [...creativeQueryKeys.all, 'publish-status'] as const,
  scheduleConfig: () => [...creativeQueryKeys.all, 'schedule-config'] as const,
}

export const useCreatives = (params?: CreativeListParams) =>
  useQuery<CreativeWorkbenchListResponse>({
    queryKey: creativeQueryKeys.list(params),
    queryFn: async () => {
      const response = await listCreativesApiCreativesGet({
        throwOnError: true,
        query: {
          skip: params?.skip ?? 0,
          limit: params?.limit ?? 50,
        },
      })

      return response.data ?? { total: 0, items: [] }
    },
    enabled: params?.enabled ?? true,
    retry: false,
  })

export const useCreative = (creativeId: number | undefined) =>
  useQuery<CreativeDetailResponse>({
    queryKey: creativeQueryKeys.detail(creativeId),
    queryFn: async () => {
      const response = await getCreativeApiCreativesCreativeIdGet({
        throwOnError: true,
        path: { creative_id: creativeId! },
      })

      return response.data!
    },
    enabled: creativeId !== undefined,
    retry: false,
  })

export const usePublishPoolItems = (params?: {
  skip?: number
  limit?: number
  status?: PublishPoolStatus
  creativeId?: number
  enabled?: boolean
}) =>
  useQuery<PublishPoolListResponse>({
    queryKey: creativeQueryKeys.publishPoolList(params),
    queryFn: async () => {
      const response = await listPublishPoolItemsApiCreativePublishPoolGet({
        throwOnError: true,
        query: {
          skip: params?.skip ?? 0,
          limit: params?.limit ?? 50,
          status: params?.status,
          creative_id: params?.creativeId,
        },
      })

      return response.data ?? { total: 0, items: [] }
    },
    enabled: params?.enabled ?? true,
    retry: false,
  })

export const usePublishStatus = () =>
  useQuery<PublishStatusResponse | undefined>({
    queryKey: creativeQueryKeys.publishStatus(),
    queryFn: async () => {
      const response = await getPublishStatusApiPublishStatusGet({
        throwOnError: true,
      })
      return response.data
    },
    retry: false,
  })

export const useCreateCreative = () => {
  const queryClient = useQueryClient()

  return useMutation<CreativeDetailResponse, Error, CreativeCreateRequest>({
    mutationFn: async (body) => {
      const response = await createCreativeApiCreativesPost({
        body,
        throwOnError: true,
      })

      return response.data!
    },
    onSuccess: async (creative) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: creativeQueryKeys.lists() }),
        queryClient.invalidateQueries({ queryKey: creativeQueryKeys.detail(creative.id) }),
      ])
    },
  })
}

export const useUpdateCreative = (creativeId: number | undefined) => {
  const queryClient = useQueryClient()

  return useMutation<CreativeDetailResponse, Error, CreativeUpdateRequest>({
    mutationFn: async (body) => {
      const response = await updateCreativeApiCreativesCreativeIdPatch({
        path: { creative_id: creativeId! },
        body,
        throwOnError: true,
      })

      return response.data!
    },
    onSuccess: async () => {
      if (creativeId !== undefined) {
        await invalidateCreativeQueries(queryClient, creativeId)
      }
    },
  })
}

export const useSubmitCreativeComposition = (creativeId: number | undefined) => {
  const queryClient = useQueryClient()

  return useMutation<CreativeComposeSubmitResponse, Error>({
    mutationFn: async () => {
      const response = await submitCreativeCompositionApiCreativesCreativeIdSubmitCompositionPost({
        path: { creative_id: creativeId! },
        throwOnError: true,
      })

      return response.data!
    },
    onSuccess: async () => {
      if (creativeId !== undefined) {
        await Promise.all([
          invalidateCreativeQueries(queryClient, creativeId),
          queryClient.invalidateQueries({ queryKey: creativeQueryKeys.publishPool() }),
        ])
      }
    },
  })
}

export const useScheduleConfig = () =>
  useQuery<ScheduleConfigResponse | undefined>({
    queryKey: creativeQueryKeys.scheduleConfig(),
    queryFn: async () => {
      const response = await getScheduleConfigApiScheduleConfigGet({
        throwOnError: true,
      })
      return response.data
    },
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
