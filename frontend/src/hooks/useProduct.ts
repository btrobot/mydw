/**
 * Product Hooks — /api/products
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listProductsApiProductsGet,
  createProductApiProductsPost,
  deleteProductApiProductsProductIdDelete,
  updateProductApiProductsProductIdPut,
  getProductApiProductsProductIdGet,
  getProductMaterialsApiProductsProductIdMaterialsGet,
  parseProductMaterialsApiProductsProductIdParseMaterialsPost,
} from '@/api'
import type {
  ProductCreate,
  ProductDetailResponse,
  ProductListResponse,
  ProductMaterialsResponse,
  ProductResponse,
} from '@/api'

export const useProducts = (name?: string) =>
  useQuery<ProductResponse[]>({
    queryKey: ['products-v2', name],
    queryFn: async () => {
      const response = await listProductsApiProductsGet({
        query: name ? { name } : undefined,
      })
      return (response.data as ProductListResponse).items
    },
  })

export const useBatchDeleteProducts = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (ids: number[]) => {
      await Promise.all(ids.map((id) => deleteProductApiProductsProductIdDelete({ path: { product_id: id } })))
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
      const response = await createProductApiProductsPost({ body: payload })
      return response.data!
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
      await deleteProductApiProductsProductIdDelete({ path: { product_id: productId } })
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
      const response = await updateProductApiProductsProductIdPut({
        path: { product_id: id },
        body: { name },
      })
      return response.data!
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
      const response = await getProductApiProductsProductIdGet({ path: { product_id: id! } })
      return response.data!
    },
    enabled: id !== undefined,
  })

/** GET /products/{id}/materials — 获取商品素材（用于素材篮快速导入） */
export const useProductMaterials = (id: number | undefined) =>
  useQuery<ProductMaterialsResponse>({
    queryKey: ['product-materials', id],
    queryFn: async () => {
      const response = await getProductMaterialsApiProductsProductIdMaterialsGet({ path: { product_id: id! } })
      return response.data!
    },
    enabled: id !== undefined,
  })

export const useParseProductMaterials = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (productId: number) => {
      const response = await parseProductMaterialsApiProductsProductIdParseMaterialsPost({
        path: { product_id: productId },
      })
      return response.data as ProductDetailResponse
    },
    onSuccess: (_data, productId) => {
      queryClient.invalidateQueries({ queryKey: ['product', productId] })
      queryClient.invalidateQueries({ queryKey: ['products-v2'] })
    },
  })
}
