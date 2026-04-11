/**
 * Copywriting Hooks — /api/copywritings
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listCopywritingsApiCopywritingsGet,
  createCopywritingApiCopywritingsPost,
  deleteCopywritingApiCopywritingsCopywritingIdDelete,
  updateCopywritingApiCopywritingsCopywritingIdPut,
  importCopywritingsApiCopywritingsImportPost,
  batchDeleteCopywritingsApiCopywritingsBatchDeletePost,
} from '@/api'
import type {
  CopywritingCreate,
  CopywritingListResponse,
  CopywritingResponse,
} from '@/api'
import type { BatchDeleteResponse } from '@/types/material'

export const useCopywritings = (params?: { keyword?: string; sourceType?: string; productId?: number }) =>
  useQuery<CopywritingResponse[]>({
    queryKey: ['copywritings', params],
    queryFn: async () => {
      const response = await listCopywritingsApiCopywritingsGet({
        query: {
          keyword: params?.keyword,
          source_type: params?.sourceType,
          product_id: params?.productId,
        },
      })
      return (response.data as CopywritingListResponse).items
    },
  })

export const useCreateCopywriting = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CopywritingCreate) => {
      const response = await createCopywritingApiCopywritingsPost({ body: payload })
      return response.data!
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
      await deleteCopywritingApiCopywritingsCopywritingIdDelete({ path: { copywriting_id: copywritingId } })
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
      const response = await updateCopywritingApiCopywritingsCopywritingIdPut({
        path: { copywriting_id: id },
        body: payload,
      })
      return response.data!
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
      const response = await importCopywritingsApiCopywritingsImportPost({
        body: { file },
        query: productId !== undefined ? { product_id: productId } : undefined,
      })
      return response.data as ImportResult
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['copywritings'] })
    },
  })
}

export const useBatchDeleteCopywritings = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (ids: number[]) => {
      const response = await batchDeleteCopywritingsApiCopywritingsBatchDeletePost({ body: { ids } })
      return response.data as BatchDeleteResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['copywritings'] })
    },
  })
}
