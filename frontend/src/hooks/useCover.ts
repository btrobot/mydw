/**
 * Cover Hooks — /api/covers
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { CoverResponse } from '@/types/material'

export const useCovers = (videoId?: number) =>
  useQuery<CoverResponse[]>({
    queryKey: ['covers', videoId],
    queryFn: async () => {
      const params = videoId !== undefined ? { video_id: videoId } : {}
      const { data } = await api.get<CoverResponse[]>('/covers', { params })
      return data
    },
  })

export const useUploadCover = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ file, videoId }: { file: File; videoId?: number }) => {
      const formData = new FormData()
      formData.append('file', file)
      const params = videoId !== undefined ? { video_id: videoId } : {}
      const { data } = await api.post<CoverResponse>('/covers/upload', formData, {
        params,
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
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
      await api.delete(`/covers/${coverId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['covers'] })
    },
  })
}
