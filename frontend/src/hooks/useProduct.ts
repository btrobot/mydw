/**
 * Product Hooks — /api/products
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { ProductResponse, ProductListResponse, ProductCreate, CoverResponse, TopicResponse, TopicListResponse } from '@/types/material'

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

/** SP7-06: 商品更新 */
export const useUpdateProduct = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, ...payload }: { id: number; name?: string; dewu_url?: string }) => {
      const { data } = await api.put<ProductResponse>(`/products/${id}`, payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products-v2'] })
    },
  })
}

/** GET /products/{id} — 单个商品详情 */
export const useProduct = (id: number | undefined) =>
  useQuery<ProductResponse>({
    queryKey: ['product', id],
    queryFn: async () => {
      const { data } = await api.get<ProductResponse>(`/products/${id}`)
      return data
    },
    enabled: id !== undefined,
  })

/** GET /products/{id}/covers — 商品封面列表 */
export const useProductCovers = (id: number | undefined) =>
  useQuery<CoverResponse[]>({
    queryKey: ['product-covers', id],
    queryFn: async () => {
      const { data } = await api.get<CoverResponse[]>(`/products/${id}/covers`)
      return data
    },
    enabled: id !== undefined,
  })

/** GET /products/{id}/topics — 商品话题列表 */
export const useProductTopics = (id: number | undefined) =>
  useQuery<TopicResponse[]>({
    queryKey: ['product-topics', id],
    queryFn: async () => {
      const { data } = await api.get<TopicListResponse>(`/products/${id}/topics`)
      return data.items
    },
    enabled: id !== undefined,
  })
