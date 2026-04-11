/**
 * Audio Hooks — /api/audios
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listAudiosApiAudiosGet,
  uploadAudioApiAudiosUploadPost,
  deleteAudioApiAudiosAudioIdDelete,
  batchDeleteAudiosApiAudiosBatchDeletePost,
} from '@/api'
import type { AudioResponse } from '@/api'
import type { BatchDeleteResponse } from '@/types/material'

export const useAudios = (keyword?: string) =>
  useQuery<AudioResponse[]>({
    queryKey: ['audios', keyword],
    queryFn: async () => {
      const response = await listAudiosApiAudiosGet({
        query: keyword ? { keyword } : undefined,
      })
      return (response.data ?? []) as AudioResponse[]
    },
  })

export const useUploadAudio = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const response = await uploadAudioApiAudiosUploadPost({
        body: { file },
      })
      return response.data!
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
      await deleteAudioApiAudiosAudioIdDelete({ path: { audio_id: audioId } })
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
      const response = await batchDeleteAudiosApiAudiosBatchDeletePost({ body: { ids } })
      return response.data as BatchDeleteResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audios'] })
    },
  })
}
