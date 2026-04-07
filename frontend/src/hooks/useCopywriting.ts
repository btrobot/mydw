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

/** SP7-05: 文案更新 */
export const useUpdateCopywriting = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...payload }: { id: number; content?: string; product_id?: number | null }) => {
      const { data } = await api.put<CopywritingResponse>(`/copywritings/${id}`, payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['copywritings'] })
    },
  })
}

/** SP7-08: 文案批量导入 */
interface ImportResult {
  total_lines: number
  imported: number
  skipped_empty: number
}

export const useImportCopywritings = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ file, productId }: { file: File; productId?: number }) => {
      const formData = new FormData()
      formData.append('file', file)
      const params = productId !== undefined ? { product_id: productId } : {}
      const { data } = await api.post<ImportResult>('/copywritings/import', formData, {
        params,
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['copywritings'] })
    },
  })
}
