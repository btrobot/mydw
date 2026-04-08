/**
 * Product Hooks — /api/products
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { ProductResponse, ProductDetailResponse, ProductListResponse, ProductCreate } from '@/types/material'

export const useProducts = (name?: string) =>
  useQuery<ProductResponse[]>({
    queryKey: ['products-v2', name],
    queryFn: async () => {
      const { data } = await api.get<ProductListResponse>('/products', {
        params: name ? { name } : undefined,
      })
      return data.items
    },
  })

export const useBatchDeleteProducts = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (ids: number[]) => {
      await Promise.all(ids.map((id) => api.delete(`/products/${id}`)))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products-v2'] })
    },
  })
}

export const useCreateProduct = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: ProductCreate) => {
      const { data } = await api.post<ProductResponse>('/products', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products-v2'] })
    },
  })
}

export const useDeleteProduct = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (productId: number) => {
      await api.delete(`/products/${productId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products-v2'] })
    },
  })
}

/** SP7-06: 商品更新 (name only after backend refactor) */
export const useUpdateProduct = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, name }: { id: number; name: string }) => {
      const { data } = await api.put<ProductResponse>(`/products/${id}`, { name })
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products-v2'] })
    },
  })
}

/** GET /products/{id} — 单个商品详情（含关联素材） */
export const useProduct = (id: number | undefined) =>
  useQuery<ProductDetailResponse>({
    queryKey: ['product', id],
    queryFn: async () => {
      const { data } = await api.get<ProductDetailResponse>(`/products/${id}`)
      return data
    },
    enabled: id !== undefined,
  })
