/**
 * Cover Hooks — /api/covers
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listCoversApiCoversGet,
  uploadCoverApiCoversUploadPost,
  deleteCoverApiCoversCoverIdDelete,
  extractCoverApiCoversExtractPost,
  batchDeleteCoversApiCoversBatchDeletePost,
} from '@/api'
import type { CoverResponse } from '@/api'
import type { BatchDeleteResponse } from '@/types/material'

export const useCovers = (videoId?: number) =>
  useQuery<CoverResponse[]>({
    queryKey: ['covers', videoId],
    queryFn: async () => {
      const response = await listCoversApiCoversGet({
        query: videoId !== undefined ? { video_id: videoId } : undefined,
      })
      return (response.data ?? []) as CoverResponse[]
    },
  })

export const useUploadCover = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ file, videoId }: { file: File; videoId?: number }) => {
      const response = await uploadCoverApiCoversUploadPost({
        body: { file },
        query: videoId !== undefined ? { video_id: videoId } : undefined,
      })
      return response.data!
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['covers'] })
    },
  })
}

export const useDeleteCover = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (coverId: number) => {
      await deleteCoverApiCoversCoverIdDelete({ path: { cover_id: coverId } })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['covers'] })
    },
  })
}

/** SP8-02: 封面自动提取 */
export const useExtractCover = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ videoId, timestamp }: { videoId: number; timestamp?: number }) => {
      const response = await extractCoverApiCoversExtractPost({
        body: {
          video_id: videoId,
          timestamp: timestamp ?? 1.0,
        },
      })
      return response.data!
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['covers'] })
    },
  })
}

export const useBatchDeleteCovers = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (ids: number[]) => {
      const response = await batchDeleteCoversApiCoversBatchDeletePost({ body: { ids } })
      return response.data as BatchDeleteResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['covers'] })
    },
  })
}
