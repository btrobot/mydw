/**
 * Publish Hooks - 发布相关的 React Query hooks
 */
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  controlPublishApiPublishControlPost,
  getPublishStatusApiPublishStatusGet,
  getPublishLogsApiPublishLogsGet,
} from '@/api'

import type {
  PublishStatusResponse,
  PublishControlRequest,
  SystemLogListResponse,
} from '@/api'

export const useControlPublish = () =>
  useMutation({
    mutationFn: async (data: PublishControlRequest) => {
      const response = await controlPublishApiPublishControlPost({ body: data })
      return response.data
    },
  })

export const usePublishStatus = () =>
  useQuery<PublishStatusResponse>({
    queryKey: ['publishStatus'],
    queryFn: async () => {
      const response = await getPublishStatusApiPublishStatusGet()
      return response.data!
    },
    refetchInterval: 5000,
  })

export const usePublishLogs = () =>
  useQuery<SystemLogListResponse>({
    queryKey: ['publishLogs'],
    queryFn: async () => {
      const response = await getPublishLogsApiPublishLogsGet()
      return (response.data ?? { total: 0, items: [] }) as SystemLogListResponse
    },
  })
