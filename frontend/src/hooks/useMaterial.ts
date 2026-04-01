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
  listProductsApiSystemProductsGet,
  createProductApiSystemProductsPost,
  deleteProductApiSystemProductsProductIdDelete,
} from '@/api'

import type {
  MaterialResponse,
  MaterialStatsResponse,
  MaterialCreate,
  MaterialUpdate,
  ScanRequest,
  ProductListResponse,
  ProductCreate,
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
      return response.data!
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
      return response.data!
    },
  })

// ============ Product Hooks ============

export const useProducts = () =>
  useQuery<ProductListResponse>({
    queryKey: ['products'],
    queryFn: async () => {
      const response = await listProductsApiSystemProductsGet()
      return response.data ?? { total: 0, items: [] }
    },
  })

export const useCreateProduct = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: ProductCreate) => {
      const response = await createProductApiSystemProductsPost({ body: data })
      return response.data
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
      await deleteProductApiSystemProductsProductIdDelete({ path: { product_id: productId } })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}
