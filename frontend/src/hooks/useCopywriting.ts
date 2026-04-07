/**
 * Copywriting Hooks — /api/copywritings
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { CopywritingResponse, CopywritingListResponse, CopywritingCreate } from '@/types/material'

export const useCopywritings = (productId?: number) =>
  useQuery<CopywritingResponse[]>({
    queryKey: ['copywritings', productId],
    queryFn: async () => {
      const params = productId !== undefined ? { product_id: productId } : {}
      const { data } = await api.get<CopywritingListResponse>('/copywritings', { params })
      return data.items
    },
  })

export const useCreateCopywriting = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CopywritingCreate) => {
      const { data } = await api.post<CopywritingResponse>('/copywritings', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['copywritings'] })
    },
  })
}

export const useDeleteCopywriting = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (copywritingId: number) => {
      await api.delete(`/copywritings/${copywritingId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['copywritings'] })
    },
  })
}
