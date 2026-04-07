/**
 * Video Hooks — /api/videos
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { VideoResponse, VideoListResponse, VideoCreate, BatchDeleteResponse } from '@/types/material'

interface UseVideosOptions {
  keyword?: string
  productId?: number
}

export const useVideos = (options?: UseVideosOptions) =>
  useQuery<VideoResponse[]>({
    queryKey: ['videos', options],
    queryFn: async () => {
      const params: Record<string, string | number> = {}
      if (options?.keyword) params.keyword = options.keyword
      if (options?.productId !== undefined) params.product_id = options.productId
      const { data } = await api.get<VideoListResponse>('/videos', { params })
      return data.items
    },
  })

export const useCreateVideo = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: VideoCreate) => {
      const { data } = await api.post<VideoResponse>('/videos', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}

export const useDeleteVideo = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (videoId: number) => {
      await api.delete(`/videos/${videoId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}

/** SP6-02: 视频文件上传 */
export const useUploadVideo = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ file, productId }: { file: File; productId?: number }) => {
      const formData = new FormData()
      formData.append('file', file)
      const params = productId !== undefined ? { product_id: productId } : {}
      const { data } = await api.post<VideoResponse>('/videos/upload', formData, {
        params,
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}

export const useBatchDeleteVideos = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (ids: number[]) => {
      const { data } = await api.post<BatchDeleteResponse>('/videos/batch-delete', { ids })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}

/** SP6-03: 目录扫描导入 */
interface ScanResult {
  total_scanned: number
  new_imported: number
  skipped: number
  failed: number
  details: string[]
}

export const useScanVideos = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<ScanResult>('/videos/scan')
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}
