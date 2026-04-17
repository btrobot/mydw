import { useMutation, useQueryClient } from '@tanstack/react-query'

import { submitAiClipWorkflowApiCreativeWorkflowsCreativeIdAiClipSubmitPost } from '@/api'
import type {
  CreativeAiClipWorkflowResponse,
  CreativeAiClipWorkflowSubmitRequest,
} from '@/api'

import { creativeQueryKeys } from './useCreatives'

export const useSubmitAiClipWorkflow = (creativeId: number | undefined) => {
  const queryClient = useQueryClient()

  return useMutation<CreativeAiClipWorkflowResponse | undefined, Error, CreativeAiClipWorkflowSubmitRequest>({
    mutationFn: async (body) => {
      const response = await submitAiClipWorkflowApiCreativeWorkflowsCreativeIdAiClipSubmitPost({
        path: { creative_id: creativeId! },
        body,
      })

      return response.data
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: creativeQueryKeys.lists() }),
        queryClient.invalidateQueries({ queryKey: creativeQueryKeys.publishPool() }),
        creativeId !== undefined
          ? queryClient.invalidateQueries({ queryKey: creativeQueryKeys.detail(creativeId) })
          : Promise.resolve(),
      ])
    },
  })
}
