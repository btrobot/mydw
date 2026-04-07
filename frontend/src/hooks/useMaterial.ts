/**
 * Material Hooks - 素材相关的 React Query hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listMaterialsApiMaterialsGet,
  createMaterialApiMaterialsPost,
  getMaterialApiMaterialsMaterialIdGet,
  updateMaterialApiMaterialsMaterialIdPut,
  deleteMaterialApiMaterialsMaterialIdDelete,
  scanMaterialsApiMaterialsScanPost,
  importMaterialsApiMaterialsImportPost,
  deleteAllMaterialsApiMaterialsDelete,
  getMaterialStatsApiMaterialsStatsGet,
} from '@/api'

import type {
  MaterialResponse,
  MaterialStatsResponse,
  MaterialCreate,
  MaterialUpdate,
  ScanRequest,
} from '@/api'

export const useMaterials = () =>
  useQuery<MaterialResponse[]>({
    queryKey: ['materials'],
    queryFn: async () => {
      const response = await listMaterialsApiMaterialsGet()
      // 返回 items 数组或空数组
      const data = response.data
      if (Array.isArray(data)) return data
      if (data && 'items' in data) return (data as { items: MaterialResponse[] }).items
      return []
    },
  })

export const useMaterial = (materialId: number) =>
  useQuery<MaterialResponse>({
    queryKey: ['material', materialId],
    queryFn: async () => {
      const response = await getMaterialApiMaterialsMaterialIdGet({ path: { material_id: materialId } })
      if (!response.data) throw new Error('素材不存在')
      return response.data as MaterialResponse
    },
    enabled: !!materialId,
  })

export const useCreateMaterial = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: MaterialCreate) => {
      const response = await createMaterialApiMaterialsPost({ body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
    },
  })
}

export const useUpdateMaterial = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ materialId, data }: { materialId: number; data: MaterialUpdate }) => {
      const response = await updateMaterialApiMaterialsMaterialIdPut({ path: { material_id: materialId }, body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
    },
  })
}

export const useDeleteMaterial = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (materialId: number) => {
      await deleteMaterialApiMaterialsMaterialIdDelete({ path: { material_id: materialId } })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
    },
  })
}

export const useScanMaterials = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: ScanRequest) => {
      const response = await scanMaterialsApiMaterialsScanPost({ body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
    },
  })
}

export const useImportMaterials = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: { type?: string }) => {
      const response = await importMaterialsApiMaterialsImportPost({ query: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
    },
  })
}

export const useDeleteAllMaterials = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      await deleteAllMaterialsApiMaterialsDelete()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
    },
  })
}

export const useMaterialStats = () =>
  useQuery<MaterialStatsResponse>({
    queryKey: ['materialStats'],
    queryFn: async () => {
      const response = await getMaterialStatsApiMaterialsStatsGet()
      if (!response.data) throw new Error('获取统计数据失败')
      return response.data as MaterialStatsResponse
    },
  })

// ============ Product Hooks (迁移到 /materials/products) ============

export interface ProductItem {
  id: number
  name: string
  link?: string | null
  description?: string | null
  created_at: string
}

export const useProducts = () =>
  useQuery<ProductItem[]>({
    queryKey: ['products'],
    queryFn: async () => {
      const { api } = await import('@/services/api')
      const { data } = await api.get<{ total: number; items: ProductItem[] }>('/materials/products')
      return data?.items ?? []
    },
  })

export const useCreateProduct = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: { name: string; link?: string }) => {
      const { api } = await import('@/services/api')
      const { data: result } = await api.post('/materials/products', data)
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}

export const useDeleteProduct = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (productId: number) => {
      const { api } = await import('@/services/api')
      await api.delete(`/materials/products/${productId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}
