/**
 * AI Clip Hooks - AI 剪辑相关的 React Query hooks
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getVideoInfoApiAiVideoInfoGet,
  detectHighlightsApiAiDetectHighlightsGet,
  smartClipApiAiSmartClipPost,
  trimVideoApiAiTrimPost,
  addAudioApiAiAddAudioPost,
  addCoverApiAiAddCoverPost,
  fullPipelineApiAiFullPipelinePost,
} from '@/api'

import type {
  VideoInfoResponse,
  DetectHighlightsResponse,
  SmartClipRequest,
  TrimVideoRequest,
  AddAudioRequest,
  AddCoverRequest,
  FullPipelineRequest,
} from '@/api'

export const useVideoInfo = () =>
  useMutation<VideoInfoResponse, unknown, { video_path: string }>({
    mutationFn: async (data) => {
      const response = await getVideoInfoApiAiVideoInfoGet({ query: data })
      return response.data!
    },
  })

export const useDetectHighlights = () =>
  useMutation<DetectHighlightsResponse, unknown, { video_path: string }>({
    mutationFn: async (data) => {
      const response = await detectHighlightsApiAiDetectHighlightsGet({ query: data })
      return response.data!
    },
  })

export const useSmartClip = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: SmartClipRequest) => {
      const response = await smartClipApiAiSmartClipPost({ body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clips'] })
    },
  })
}

export const useTrimVideo = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: TrimVideoRequest) => {
      const response = await trimVideoApiAiTrimPost({ body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clips'] })
    },
  })
}

export const useAddAudio = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: AddAudioRequest) => {
      const response = await addAudioApiAiAddAudioPost({ body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clips'] })
    },
  })
}

export const useAddCover = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: AddCoverRequest) => {
      const response = await addCoverApiAiAddCoverPost({ body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clips'] })
    },
  })
}

export const useFullPipeline = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: FullPipelineRequest) => {
      const response = await fullPipelineApiAiFullPipelinePost({ body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clips'] })
    },
  })
}
