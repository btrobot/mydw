/**
 * Product Hooks — /api/products
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { ProductResponse, ProductListResponse, ProductCreate } from '@/types/material'

export const useProducts = () =>
  useQuery<ProductResponse[]>({
    queryKey: ['products-v2'],
    queryFn: async () => {
      const { data } = await api.get<ProductListResponse>('/products')
      return data.items
    },
  })

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
