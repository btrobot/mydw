import type {
  CreativeCoverMode,
  CreativeCopywritingMode,
  CreativeCurrentCoverAssetType,
  CreativeDetailResponse,
  CreativeInputItemResponse,
  CreativeInputItemWrite,
  CreativeProductNameMode,
} from '@/api'

export const creativeInputMaterialMeta = {
  video: { label: '视频素材' },
  copywriting: { label: '文案素材' },
  cover: { label: '封面素材' },
  audio: { label: '音频素材' },
  topic: { label: '话题素材' },
} as const

export type CreativeInputMaterialType = keyof typeof creativeInputMaterialMeta

export type CreativeAuthoringInputItemFormValue = {
  material_type: CreativeInputMaterialType
  material_id?: number
  role?: string
  trim_in?: number | null
  trim_out?: number | null
  slot_duration_seconds?: number | null
  enabled?: boolean
}

export type CreativeAuthoringFormValues = {
  title?: string
  profile_id?: number
  subject_product_id?: number
  subject_product_name_snapshot?: string
  main_copywriting_text?: string
  current_product_name?: string
  product_name_mode?: CreativeProductNameMode
  current_cover_asset_type?: CreativeCurrentCoverAssetType
  current_cover_asset_id?: number
  cover_mode?: CreativeCoverMode
  current_copywriting_id?: number
  current_copywriting_text?: string
  copywriting_mode?: CreativeCopywritingMode
  target_duration_seconds?: number
  input_items: CreativeAuthoringInputItemFormValue[]
}

const normalizeInputItem = (
  item: CreativeInputItemResponse | Record<string, unknown>,
): CreativeAuthoringInputItemFormValue => ({
  material_type: String(item.material_type) as CreativeInputMaterialType,
  material_id:
    item.material_id === undefined || item.material_id === null
      ? undefined
      : Number(item.material_id),
  role: typeof item.role === 'string' ? item.role : undefined,
  trim_in:
    item.trim_in === undefined || item.trim_in === null ? undefined : Number(item.trim_in),
  trim_out:
    item.trim_out === undefined || item.trim_out === null ? undefined : Number(item.trim_out),
  slot_duration_seconds:
    item.slot_duration_seconds === undefined || item.slot_duration_seconds === null
      ? undefined
      : Number(item.slot_duration_seconds),
  enabled: item.enabled === undefined ? true : Boolean(item.enabled),
})

export const getCreativeAuthoringInputItems = (
  creative: Pick<CreativeDetailResponse, 'input_items'>,
): CreativeAuthoringInputItemFormValue[] => {
  const inputItems = creative.input_items ?? []

  return [...inputItems]
    .sort((left, right) => {
      const sequenceDelta = (left.sequence ?? 0) - (right.sequence ?? 0)
      if (sequenceDelta !== 0) {
        return sequenceDelta
      }
      return (left.instance_no ?? 0) - (right.instance_no ?? 0)
    })
    .map(normalizeInputItem)
}

export const toCreativeAuthoringFormValues = (
  creative: CreativeDetailResponse,
): CreativeAuthoringFormValues => ({
  title: creative.title ?? undefined,
  profile_id: creative.input_orchestration?.profile_id ?? undefined,
  subject_product_id: creative.subject_product_id ?? undefined,
  subject_product_name_snapshot: creative.subject_product_name_snapshot ?? undefined,
  main_copywriting_text: creative.main_copywriting_text ?? undefined,
  current_product_name: creative.current_product_name ?? creative.subject_product_name_snapshot ?? undefined,
  product_name_mode: creative.product_name_mode ?? undefined,
  current_cover_asset_type: creative.current_cover_asset_type ?? undefined,
  current_cover_asset_id: creative.current_cover_asset_id ?? undefined,
  cover_mode: creative.cover_mode ?? undefined,
  current_copywriting_id: creative.current_copywriting_id ?? undefined,
  current_copywriting_text: creative.current_copywriting_text ?? creative.main_copywriting_text ?? undefined,
  copywriting_mode: creative.copywriting_mode ?? undefined,
  target_duration_seconds: creative.target_duration_seconds ?? undefined,
  input_items: getCreativeAuthoringInputItems(creative),
})

export const buildCreativeAuthoringPayload = (
  values: CreativeAuthoringFormValues,
): {
  title?: string
  profile_id: number | null
  subject_product_id: number | null
  subject_product_name_snapshot: string | null
  main_copywriting_text: string | null
  current_product_name: string | null
  product_name_mode: CreativeProductNameMode | null
  current_cover_asset_type: CreativeCurrentCoverAssetType | null
  current_cover_asset_id: number | null
  cover_mode: CreativeCoverMode | null
  current_copywriting_id: number | null
  current_copywriting_text: string | null
  copywriting_mode: CreativeCopywritingMode | null
  target_duration_seconds: number | null
  input_items: Array<CreativeInputItemWrite>
} => {
  const currentProductName = values.current_product_name?.trim() || null
  const currentCopywritingText = values.current_copywriting_text?.trim() || null
  const productNameMode = values.product_name_mode
    ?? (values.subject_product_id ? 'follow_primary_product' : (currentProductName ? 'manual' : null))
  const coverMode = values.cover_mode
    ?? (values.current_cover_asset_id !== undefined && values.current_cover_asset_id !== null
      ? 'manual'
      : (values.subject_product_id ? 'default_from_primary_product' : null))
  const currentCoverAssetId = coverMode === 'default_from_primary_product'
    ? null
    : (values.current_cover_asset_id ?? null)
  const currentCoverAssetType = currentCoverAssetId === null
    ? null
    : (values.current_cover_asset_type ?? 'cover')
  const currentCopywritingId = values.current_copywriting_id ?? null
  const copywritingMode = values.copywriting_mode
    ?? (currentCopywritingId !== null ? 'adopted_candidate' : (currentCopywritingText ? 'manual' : null))

  return {
    title: values.title?.trim() ? values.title.trim() : undefined,
    profile_id: values.profile_id ?? null,
    subject_product_id: values.subject_product_id ?? null,
    subject_product_name_snapshot: currentProductName,
    main_copywriting_text: currentCopywritingText,
    current_product_name: currentProductName,
    product_name_mode: productNameMode,
    current_cover_asset_type: currentCoverAssetType,
    current_cover_asset_id: currentCoverAssetId,
    cover_mode: coverMode,
    current_copywriting_id: currentCopywritingId,
    current_copywriting_text: currentCopywritingText,
    copywriting_mode: copywritingMode,
    target_duration_seconds: values.target_duration_seconds ?? null,
    input_items: (values.input_items ?? [])
      .filter((item) => item.material_type && item.material_id !== undefined && item.material_id !== null)
      .map((item, index) => ({
        material_type: item.material_type,
        material_id: Number(item.material_id),
        role: item.role?.trim() || null,
        sequence: index + 1,
        trim_in: item.trim_in ?? null,
        trim_out: item.trim_out ?? null,
        slot_duration_seconds: item.slot_duration_seconds ?? null,
        enabled: item.enabled ?? true,
      })),
  }
}

export const countEnabledCreativeInputItems = (
  items: Array<Pick<CreativeInputItemResponse, 'enabled'> | CreativeAuthoringInputItemFormValue> | undefined,
): number => (items ?? []).filter((item) => item.enabled !== false).length

export const formatCreativeDuration = (value?: number | null): string =>
  value && value > 0 ? `${value} 秒` : '未设定时长'
