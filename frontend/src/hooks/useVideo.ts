/**
 * Video Hooks — /api/videos
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listVideosApiVideosGet,
  createVideoApiVideosPost,
  deleteVideoApiVideosVideoIdDelete,
  uploadVideoApiVideosUploadPost,
  batchDeleteVideosApiVideosBatchDeletePost,
  scanVideosApiVideosScanPost,
  getVideoApiVideosVideoIdGet,
} from '@/api'
import type {
  VideoCreate,
  VideoListResponse,
  VideoResponse,
} from '@/api'
import type { BatchDeleteResponse } from '@/types/material'

interface UseVideosOptions {
  keyword?: string
  productId?: number
}

export const useVideo = (id: number | undefined) =>
  useQuery<VideoResponse>({
    queryKey: ['video', id],
    queryFn: async () => {
      const response = await getVideoApiVideosVideoIdGet({ path: { video_id: id! } })
      return response.data!
    },
    enabled: id !== undefined,
  })

export const useVideos = (options?: UseVideosOptions) =>
  useQuery<VideoResponse[]>({
    queryKey: ['videos', options],
    queryFn: async () => {
      const response = await listVideosApiVideosGet({
        query: {
          keyword: options?.keyword,
          product_id: options?.productId,
        },
      })
      return (response.data as VideoListResponse).items
    },
  })

export const useCreateVideo = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: VideoCreate) => {
      const response = await createVideoApiVideosPost({ body: payload })
      return response.data!
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
      await deleteVideoApiVideosVideoIdDelete({ path: { video_id: videoId } })
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
      const response = await uploadVideoApiVideosUploadPost({
        body: { file },
        query: productId !== undefined ? { product_id: productId } : undefined,
      })
      return response.data!
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
      const response = await batchDeleteVideosApiVideosBatchDeletePost({ body: { ids } })
      return response.data as BatchDeleteResponse
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
      const response = await scanVideosApiVideosScanPost()
      return response.data as ScanResult
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}
