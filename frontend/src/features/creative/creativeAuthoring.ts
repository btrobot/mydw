import type {
  CreativeCandidateItemResponse,
  CreativeCandidateItemWrite,
  CreativeCandidateSourceKind,
  CreativeCandidateStatus,
  CreativeCandidateType,
  CreativeCoverMode,
  CreativeCopywritingMode,
  CreativeCurrentCoverAssetType,
  CreativeDetailResponse,
  CreativeInputItemResponse,
  CreativeInputItemWrite,
  CreativeProductLinkResponse,
  CreativeProductLinkSourceMode,
  CreativeProductLinkWrite,
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
export const creativeSelectedMediaMeta = {
  video: creativeInputMaterialMeta.video,
  audio: creativeInputMaterialMeta.audio,
} as const

export type CreativeSelectedMediaType = keyof typeof creativeSelectedMediaMeta
export type CreativeAuthoringCandidateType = Exclude<CreativeCandidateType, never>

export const creativeCandidateMeta: Record<CreativeAuthoringCandidateType, { label: string; adoptLabel?: string }> = {
  cover: { label: '封面候选', adoptLabel: '采用为当前封面' },
  copywriting: { label: '文案候选', adoptLabel: '采用为当前文案' },
  video: { label: '视频候选' },
  audio: { label: '音频候选' },
}

export type CreativeAuthoringInputItemFormValue = {
  material_type: CreativeSelectedMediaType
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
  product_links: CreativeAuthoringProductLinkFormValue[]
  candidate_items: CreativeAuthoringCandidateItemFormValue[]
  input_items: CreativeAuthoringInputItemFormValue[]
}

export type CreativeAuthoringProductLinkFormValue = {
  product_id?: number
  is_primary?: boolean
  enabled?: boolean
  source_mode?: CreativeProductLinkSourceMode
}

export type CreativeAuthoringCandidateItemFormValue = {
  candidate_type?: CreativeCandidateType
  asset_id?: number
  source_kind?: CreativeCandidateSourceKind
  source_product_id?: number
  source_ref?: string
  enabled?: boolean
  status?: CreativeCandidateStatus
  asset_name?: string
  asset_excerpt?: string
}

const normalizeInputItem = (
  item: CreativeInputItemResponse | Record<string, unknown>,
): CreativeAuthoringInputItemFormValue => ({
  material_type: String(item.material_type) as CreativeSelectedMediaType,
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

export const isCreativeSelectedMediaType = (value: unknown): value is CreativeSelectedMediaType =>
  value === 'video' || value === 'audio'

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
    .filter((item) => isCreativeSelectedMediaType(item.material_type))
    .map(normalizeInputItem)
}

const normalizeProductLink = (
  item: CreativeProductLinkResponse | Record<string, unknown>,
): CreativeAuthoringProductLinkFormValue => ({
  product_id:
    item.product_id === undefined || item.product_id === null
      ? undefined
      : Number(item.product_id),
  is_primary: item.is_primary === undefined ? false : Boolean(item.is_primary),
  enabled: item.enabled === undefined ? true : Boolean(item.enabled),
  source_mode:
    typeof item.source_mode === 'string'
      ? item.source_mode as CreativeProductLinkSourceMode
      : undefined,
})

const normalizeCandidateItem = (
  item: CreativeCandidateItemResponse | Record<string, unknown>,
): CreativeAuthoringCandidateItemFormValue => ({
  candidate_type:
    typeof item.candidate_type === 'string'
      ? item.candidate_type as CreativeCandidateType
      : undefined,
  asset_id:
    item.asset_id === undefined || item.asset_id === null
      ? undefined
      : Number(item.asset_id),
  source_kind:
    typeof item.source_kind === 'string'
      ? item.source_kind as CreativeCandidateSourceKind
      : undefined,
  source_product_id:
    item.source_product_id === undefined || item.source_product_id === null
      ? undefined
      : Number(item.source_product_id),
  source_ref: typeof item.source_ref === 'string' ? item.source_ref : undefined,
  enabled: item.enabled === undefined ? true : Boolean(item.enabled),
  status:
    typeof item.status === 'string'
      ? item.status as CreativeCandidateStatus
      : undefined,
  asset_name: typeof item.asset_name === 'string' ? item.asset_name : undefined,
  asset_excerpt: typeof item.asset_excerpt === 'string' ? item.asset_excerpt : undefined,
})

const normalizeAuthoringProductLinks = (
  productLinks: CreativeAuthoringProductLinkFormValue[] | undefined,
): Array<CreativeProductLinkWrite> => {
  const normalizedLinks = (productLinks ?? [])
    .filter((item) => item.product_id !== undefined && item.product_id !== null)
    .map((item, index) => ({
      product_id: Number(item.product_id),
      sort_order: index + 1,
      is_primary: Boolean(item.is_primary),
      enabled: item.enabled ?? true,
      source_mode: item.source_mode ?? 'manual_add',
    }))

  if (normalizedLinks.length > 0 && !normalizedLinks.some((item) => item.is_primary)) {
    normalizedLinks[0].is_primary = true
  }

  return normalizedLinks
}

const normalizeAuthoringCandidateItems = (
  candidateItems: CreativeAuthoringCandidateItemFormValue[] | undefined,
): Array<CreativeCandidateItemWrite> => (
  (candidateItems ?? [])
    .filter(
      (item): item is CreativeAuthoringCandidateItemFormValue & { candidate_type: CreativeCandidateType; asset_id: number } =>
        item.candidate_type !== undefined
        && item.asset_id !== undefined
        && item.asset_id !== null,
    )
    .map((item, index) => ({
      candidate_type: item.candidate_type,
      asset_id: Number(item.asset_id),
      source_kind: item.source_kind ?? 'material_library',
      source_product_id: item.source_product_id ?? null,
      source_ref: item.source_ref?.trim() || null,
      sort_order: index + 1,
      enabled: item.enabled ?? true,
      status: item.status ?? 'candidate',
    }))
)

export const getCreativeAuthoringProductLinks = (
  creative: Pick<CreativeDetailResponse, 'product_links' | 'subject_product_id'>,
): CreativeAuthoringProductLinkFormValue[] => {
  const productLinks = creative.product_links ?? []
  if (productLinks.length > 0) {
    return [...productLinks]
      .sort((left, right) => (left.sort_order ?? 0) - (right.sort_order ?? 0))
      .map(normalizeProductLink)
  }
  if (creative.subject_product_id !== undefined && creative.subject_product_id !== null) {
    return [{ product_id: Number(creative.subject_product_id), is_primary: true, enabled: true, source_mode: 'import_bootstrap' }]
  }
  return []
}

export const getCreativeAuthoringCandidateItems = (
  creative: Pick<CreativeDetailResponse, 'candidate_items'>,
): CreativeAuthoringCandidateItemFormValue[] => (
  [...(creative.candidate_items ?? [])]
    .sort((left, right) => (left.sort_order ?? 0) - (right.sort_order ?? 0))
    .map(normalizeCandidateItem)
)

export const getPrimaryCreativeProductId = (
  productLinks: CreativeAuthoringProductLinkFormValue[] | undefined,
): number | undefined => {
  const normalizedLinks = normalizeAuthoringProductLinks(productLinks)
  const explicitPrimary = normalizedLinks.find((item) => item.is_primary)
  return explicitPrimary?.product_id
}

export const toCreativeAuthoringFormValues = (
  creative: CreativeDetailResponse,
): CreativeAuthoringFormValues => ({
  title: creative.title ?? undefined,
  profile_id: creative.input_orchestration?.profile_id ?? undefined,
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
  product_links: getCreativeAuthoringProductLinks(creative),
  candidate_items: getCreativeAuthoringCandidateItems(creative),
  input_items: getCreativeAuthoringInputItems(creative),
})

export const buildCreativeAuthoringPayload = (
  values: CreativeAuthoringFormValues,
): {
  title?: string
  profile_id: number | null
  subject_product_id: number | null
  product_links: Array<CreativeProductLinkWrite>
  candidate_items: Array<CreativeCandidateItemWrite>
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
  const normalizedProductLinks = normalizeAuthoringProductLinks(values.product_links)
  const normalizedCandidateItems = normalizeAuthoringCandidateItems(values.candidate_items)
  const primaryProductId = normalizedProductLinks.find((item) => item.is_primary)?.product_id ?? null
  const currentProductName = values.current_product_name?.trim() || null
  const currentCopywritingText = values.current_copywriting_text?.trim() || null
  const productNameMode = values.product_name_mode
    ?? (primaryProductId ? 'follow_primary_product' : (currentProductName ? 'manual' : null))
  const coverMode = values.cover_mode
    ?? (values.current_cover_asset_id !== undefined && values.current_cover_asset_id !== null
      ? 'manual'
      : (primaryProductId ? 'default_from_primary_product' : null))
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
    subject_product_id: primaryProductId,
    product_links: normalizedProductLinks,
    candidate_items: normalizedCandidateItems,
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
      .filter(
        (item): item is CreativeAuthoringInputItemFormValue & { material_id: number } =>
          isCreativeSelectedMediaType(item.material_type)
          && item.material_id !== undefined
          && item.material_id !== null,
      )
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
