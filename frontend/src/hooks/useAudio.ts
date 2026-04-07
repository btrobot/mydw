/**
 * Audio Hooks — /api/audios
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { AudioResponse, BatchDeleteResponse } from '@/types/material'

export const useAudios = () =>
  useQuery<AudioResponse[]>({
    queryKey: ['audios'],
    queryFn: async () => {
      const { data } = await api.get<AudioResponse[]>('/audios')
      return data
    },
  })

export const useUploadAudio = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const { data } = await api.post<AudioResponse>('/audios/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audios'] })
    },
  })
}

export const useDeleteAudio = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (audioId: number) => {
      await api.delete(`/audios/${audioId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audios'] })
    },
  })
}

export const useBatchDeleteAudios = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (ids: number[]) => {
      const { data } = await api.post<BatchDeleteResponse>('/audios/batch-delete', { ids })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audios'] })
    },
  })
}
