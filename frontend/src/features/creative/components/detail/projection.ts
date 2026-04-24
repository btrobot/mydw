import type {
  CreativeCandidateItemResponse,
  CreativeCurrentSelectionFieldResponse,
  CreativeCurrentSelectionResponse,
  CreativeDetailPageMode,
  CreativeDetailResponse,
  CreativeFreeMaterialZoneResponse,
  CreativeProductLinkResponse,
  CreativeProductZoneResponse,
  CreativeReadinessResponse,
  CreativeReadinessState,
  CreativeSelectionState,
  CreativeZoneMaterialCandidateResponse,
} from '@/api'

type ResolvableMaterialType = 'video' | 'audio' | 'copywriting' | 'cover'

type DraftProductLink = Partial<Pick<
  CreativeProductLinkResponse,
  'product_id' | 'product_name' | 'is_primary' | 'enabled' | 'source_mode'
>> & {
  id?: number | null
  sort_order?: number
}

type DraftSelectedMediaItem = {
  material_type?: 'video' | 'audio'
  material_id?: number
  enabled?: boolean
  role?: string
  sequence?: number | null
  instance_no?: number | null
}

type DraftCandidateItem = Partial<Pick<
  CreativeCandidateItemResponse,
  | 'candidate_type'
  | 'asset_id'
  | 'asset_name'
  | 'asset_excerpt'
  | 'source_kind'
  | 'source_product_id'
  | 'source_ref'
  | 'enabled'
  | 'status'
>>

type DraftProjectionState = {
  currentProductName?: string
  currentCopywritingText?: string
  currentCopywritingId?: number
  currentCoverAssetId?: number
  currentCoverAssetType?: string
  productNameMode?: string
  coverMode?: string
  copywritingMode?: string
  productLinks?: DraftProductLink[]
  inputItems?: DraftSelectedMediaItem[]
  candidateItems?: DraftCandidateItem[]
}

export type CreativeDetailProjectionModel = {
  pageMode: CreativeDetailPageMode
  readiness: CreativeReadinessResponse
  currentSelection: CreativeCurrentSelectionResponse
  productZone: CreativeProductZoneResponse
  freeMaterialZone: CreativeFreeMaterialZoneResponse
}

type BuildCreativeDetailProjectionModelInput = {
  creative: CreativeDetailResponse
  draft?: DraftProjectionState
  resolveMaterialLabel?: (type: ResolvableMaterialType, assetId?: number | null) => string | undefined
}

const hasText = (value?: string | null): value is string => typeof value === 'string' && value.trim().length > 0

const cleanText = (value?: string | null): string | undefined => {
  if (!hasText(value)) {
    return undefined
  }
  return value.trim()
}

const toSourceLabel = (mode?: string | null): string | undefined => {
  if (!mode) {
    return undefined
  }

  const meta: Record<string, string> = {
    follow_primary_product: '跟随主题商品',
    adopted_candidate: '采用候选池',
    manual: '手工定义',
    default_from_primary_product: '主题商品默认值',
  }

  return meta[mode] ?? mode
}

const ensureSelectionField = (
  base: CreativeCurrentSelectionFieldResponse | undefined,
  overrides: Partial<CreativeCurrentSelectionFieldResponse>,
  fallbackState: CreativeSelectionState,
): CreativeCurrentSelectionFieldResponse => ({
  ...base,
  ...overrides,
  state: overrides.state ?? base?.state ?? fallbackState,
})

const sortSelectedMedia = (items: DraftSelectedMediaItem[]): DraftSelectedMediaItem[] => (
  [...items].sort((left, right) => {
    const sequenceDelta = (left.sequence ?? 0) - (right.sequence ?? 0)
    if (sequenceDelta !== 0) {
      return sequenceDelta
    }
    return (left.instance_no ?? 0) - (right.instance_no ?? 0)
  })
)

const getFallbackPageMode = (creative: CreativeDetailResponse): CreativeDetailPageMode => {
  if (creative.page_mode) {
    return creative.page_mode
  }

  if (creative.status === 'PUBLISHED') {
    return 'published_followup'
  }

  if (creative.current_version_id || creative.current_version) {
    return 'result_pending_confirm'
  }

  return 'definition'
}

const getFallbackReadinessState = (
  creative: CreativeDetailResponse,
  pageMode: CreativeDetailPageMode,
): CreativeReadinessState => {
  if (creative.readiness?.state) {
    return creative.readiness.state
  }

  if (pageMode === 'published_followup') {
    return 'published_followup'
  }

  if (pageMode === 'result_pending_confirm') {
    return 'result_pending_confirm'
  }

  if (creative.eligibility_status === 'READY_TO_COMPOSE') {
    return 'ready'
  }

  const hasAnyDefinition = Boolean(
    cleanText(creative.current_product_name)
    || cleanText(creative.current_copywriting_text)
    || creative.current_cover_asset_id
    || (creative.input_items?.length ?? 0) > 0
    || (creative.product_links?.length ?? 0) > 0,
  )

  return hasAnyDefinition ? 'partial' : 'not_started'
}

const getFallbackReadiness = (
  creative: CreativeDetailResponse,
  pageMode: CreativeDetailPageMode,
): CreativeReadinessResponse => {
  const fallbackState = getFallbackReadinessState(creative, pageMode)

  if (creative.readiness) {
    return {
      ...creative.readiness,
      state: creative.readiness.state ?? fallbackState,
      can_compose: creative.readiness.can_compose ?? creative.eligibility_status === 'READY_TO_COMPOSE',
      missing_fields: creative.readiness.missing_fields ?? creative.eligibility_reasons ?? [],
      next_action_hint:
        creative.readiness.next_action_hint
        ?? (
          fallbackState === 'ready'
            ? '当前已满足提交生成条件，可直接进入生成。'
            : pageMode === 'result_pending_confirm'
              ? '先确认当前结果是否可继续沿用，必要时再回到定义区修改。'
              : pageMode === 'published_followup'
                ? '当前已进入发布跟进阶段，可查看结果、版本和发布承接。'
                : '先补齐当前入选内容，再进入生成。'
        ),
    }
  }

  return {
    state: fallbackState,
    can_compose: creative.eligibility_status === 'READY_TO_COMPOSE',
    missing_fields: creative.eligibility_reasons ?? [],
    next_action_hint:
      fallbackState === 'ready'
        ? '当前已满足提交生成条件，可直接进入生成。'
        : pageMode === 'result_pending_confirm'
          ? '先确认当前结果是否可继续沿用，必要时再回到定义区修改。'
          : pageMode === 'published_followup'
            ? '当前已进入发布跟进阶段，可查看结果、版本和发布承接。'
            : '先补齐当前入选内容，再进入生成。',
  }
}

const getPrimaryProductLink = (
  productLinks: CreativeProductLinkResponse[],
): CreativeProductLinkResponse | undefined =>
  productLinks.find((item) => item.is_primary) ?? productLinks[0]

const normalizeDraftProductLinks = (productLinks: DraftProductLink[]): CreativeProductLinkResponse[] => (
  productLinks
    .filter((item): item is DraftProductLink & { product_id: number } => (
      item.product_id !== undefined && item.product_id !== null
    ))
    .map((item, index) => ({
      id: item.id ?? null,
      product_id: item.product_id,
      product_name: item.product_name ?? null,
      sort_order: item.sort_order ?? index + 1,
      is_primary: item.is_primary ?? index === 0,
      enabled: item.enabled ?? true,
      source_mode: item.source_mode ?? 'manual_add',
    }))
)

const toDraftCandidate = (
  item: DraftCandidateItem,
  isSelected: boolean,
  isCurrentValue: boolean,
  resolveMaterialLabel?: (type: ResolvableMaterialType, assetId?: number | null) => string | undefined,
): CreativeZoneMaterialCandidateResponse | null => {
  if (!item.candidate_type || item.asset_id === undefined || item.asset_id === null) {
    return null
  }

  return {
    candidate_type: item.candidate_type,
    asset_id: Number(item.asset_id),
    asset_name:
      cleanText(item.asset_name)
      ?? resolveMaterialLabel?.(item.candidate_type as ResolvableMaterialType, item.asset_id)
      ?? `素材 #${item.asset_id}`,
    asset_excerpt: cleanText(item.asset_excerpt) ?? null,
    source_kind: item.source_kind ?? null,
    source_product_id: item.source_product_id ?? null,
    source_ref: cleanText(item.source_ref) ?? null,
    enabled: item.enabled ?? true,
    status: item.status ?? 'candidate',
    is_selected: isSelected,
    is_current_value: isCurrentValue,
  }
}

export function buildCreativeDetailProjectionModel({
  creative,
  draft,
  resolveMaterialLabel,
}: BuildCreativeDetailProjectionModelInput): CreativeDetailProjectionModel {
  const candidateLabelByType: Record<ResolvableMaterialType, Map<number, string>> = {
    video: new Map(),
    audio: new Map(),
    copywriting: new Map(),
    cover: new Map(),
  }
  const registerCandidateLabels = (
    type: ResolvableMaterialType,
    items: Array<{ asset_id?: number | null; asset_name?: string | null }> | undefined,
  ) => {
    for (const item of items ?? []) {
      if (item.asset_id === undefined || item.asset_id === null || !cleanText(item.asset_name)) {
        continue
      }
      candidateLabelByType[type].set(Number(item.asset_id), cleanText(item.asset_name)!)
    }
  }

  registerCandidateLabels('cover', creative.product_zone?.cover_candidates)
  registerCandidateLabels('video', creative.product_zone?.video_candidates)
  registerCandidateLabels('copywriting', creative.product_zone?.copywriting_candidates)
  registerCandidateLabels('cover', creative.free_material_zone?.cover_candidates)
  registerCandidateLabels('video', creative.free_material_zone?.video_candidates)
  registerCandidateLabels('audio', creative.free_material_zone?.audio_candidates)
  registerCandidateLabels('copywriting', creative.free_material_zone?.copywriting_candidates)

  const draftProductLinks = draft?.productLinks ?? creative.product_zone?.linked_products ?? creative.product_links ?? []
  const productLinks = normalizeDraftProductLinks(draftProductLinks)
  const primaryProduct = creative.product_zone?.primary_product
  const primaryProductLink = getPrimaryProductLink(productLinks)
  const currentProductName =
    cleanText(draft?.currentProductName)
    ?? cleanText(creative.current_product_name)
    ?? cleanText(creative.subject_product_name_snapshot)
    ?? cleanText(creative.current_selection?.product_name?.value_text)
  const currentCopywritingText =
    cleanText(draft?.currentCopywritingText)
    ?? cleanText(creative.current_copywriting_text)
    ?? cleanText(creative.main_copywriting_text)
    ?? cleanText(creative.current_selection?.copywriting?.value_text)
  const currentCoverAssetId =
    draft?.currentCoverAssetId
    ?? creative.current_cover_asset_id
    ?? creative.current_selection?.cover?.asset_id
    ?? undefined
  const currentCoverAssetType =
    draft?.currentCoverAssetType
    ?? creative.current_cover_asset_type
    ?? creative.current_selection?.cover?.asset_type
    ?? 'cover'
  const currentCopywritingId =
    draft?.currentCopywritingId
    ?? creative.current_copywriting_id
    ?? creative.current_selection?.copywriting?.asset_id
    ?? undefined
  const selectionInputItems = draft?.inputItems
    ?? sortSelectedMedia(
      (creative.input_items ?? [])
        .filter((item): item is typeof item & { material_type: 'video' | 'audio' } => (
          item.material_type === 'video' || item.material_type === 'audio'
        ))
        .map((item) => ({
          material_type: item.material_type,
          material_id: item.material_id ?? undefined,
          enabled: item.enabled ?? true,
          role: item.role ?? undefined,
          sequence: item.sequence ?? undefined,
          instance_no: item.instance_no ?? undefined,
        })),
    )
  const enabledSelectionItems = sortSelectedMedia(selectionInputItems.filter((item) => item.enabled !== false))
  const selectedVideoIds = new Set(
    enabledSelectionItems
      .filter((item) => item.material_type === 'video' && item.material_id !== undefined && item.material_id !== null)
      .map((item) => Number(item.material_id)),
  )
  const selectedAudioIds = new Set(
    enabledSelectionItems
      .filter((item) => item.material_type === 'audio' && item.material_id !== undefined && item.material_id !== null)
      .map((item) => Number(item.material_id)),
  )

  const pageMode = getFallbackPageMode(creative)
  const readiness = getFallbackReadiness(creative, pageMode)

  const currentSelection: CreativeCurrentSelectionResponse = {
    product_name: currentProductName
      ? ensureSelectionField(
        creative.current_selection?.product_name,
        {
          state: 'defined',
          value_text: currentProductName,
          source_label:
            creative.current_selection?.product_name?.source_label
            ?? toSourceLabel(draft?.productNameMode ?? creative.product_name_mode),
          detached: (draft?.productNameMode ?? creative.product_name_mode) === 'manual',
        },
        'defined',
      )
      : ensureSelectionField(
        creative.current_selection?.product_name,
        {
          state: 'missing',
          source_label: creative.current_selection?.product_name?.source_label ?? '待从主题商品或手工输入定义',
        },
        'missing',
      ),
    cover: currentCoverAssetId
      ? ensureSelectionField(
        creative.current_selection?.cover,
        {
          state: 'defined',
          asset_id: currentCoverAssetId,
          asset_type: currentCoverAssetType,
          asset_name:
            creative.current_selection?.cover?.asset_name
            ?? candidateLabelByType.cover.get(currentCoverAssetId)
            ?? resolveMaterialLabel?.('cover', currentCoverAssetId)
            ?? `封面 #${currentCoverAssetId}`,
          source_label:
            creative.current_selection?.cover?.source_label
            ?? toSourceLabel(draft?.coverMode ?? creative.cover_mode),
          detached: (draft?.coverMode ?? creative.cover_mode) === 'manual',
        },
        'defined',
      )
      : ensureSelectionField(
        creative.current_selection?.cover,
        {
          state: 'missing',
          source_label: creative.current_selection?.cover?.source_label ?? '待从商品区或自由素材区选择封面',
        },
        'missing',
      ),
    copywriting: currentCopywritingText || currentCopywritingId
      ? ensureSelectionField(
        creative.current_selection?.copywriting,
        {
          state: 'defined',
          asset_id: currentCopywritingId,
          value_text: currentCopywritingText,
          asset_name:
            creative.current_selection?.copywriting?.asset_name
            ?? (currentCopywritingId ? candidateLabelByType.copywriting.get(currentCopywritingId) : undefined)
            ?? (currentCopywritingId
              ? resolveMaterialLabel?.('copywriting', currentCopywritingId) ?? `文案 #${currentCopywritingId}`
              : undefined),
          source_label:
            creative.current_selection?.copywriting?.source_label
            ?? toSourceLabel(draft?.copywritingMode ?? creative.copywriting_mode),
          detached: (draft?.copywritingMode ?? creative.copywriting_mode) === 'manual',
        },
        'defined',
      )
      : ensureSelectionField(
        creative.current_selection?.copywriting,
        {
          state: 'missing',
          source_label: creative.current_selection?.copywriting?.source_label ?? '待从商品区、自由素材区或手工输入定义文案',
        },
        'missing',
      ),
    audio: selectedAudioIds.size > 0
      ? (
        creative.current_selection?.audio
        ?? {
          state: 'defined',
          asset_id: Number(
            enabledSelectionItems.find((item) => item.material_type === 'audio' && item.material_id !== undefined)?.material_id,
          ),
          asset_type: 'audio',
          asset_name: resolveMaterialLabel?.(
            'audio',
            Number(enabledSelectionItems.find((item) => item.material_type === 'audio' && item.material_id !== undefined)?.material_id),
          ) ?? candidateLabelByType.audio.get(
            Number(enabledSelectionItems.find((item) => item.material_type === 'audio' && item.material_id !== undefined)?.material_id),
          ),
          source_label: '当前入选音频',
        }
      )
      : ensureSelectionField(
        creative.current_selection?.audio,
        {
          state: creative.current_selection?.audio?.state ?? 'missing',
          source_label: creative.current_selection?.audio?.source_label ?? '待从自由素材区选择音频',
        },
        'missing',
      ),
    videos:
      enabledSelectionItems
        .filter((item) => item.material_type === 'video' && item.material_id !== undefined && item.material_id !== null)
        .map((item, index) => ensureSelectionField(
          creative.current_selection?.videos?.find((video) => video.asset_id === item.material_id),
          {
            state: 'defined',
            asset_id: Number(item.material_id),
            asset_type: 'video',
            asset_name:
              candidateLabelByType.video.get(Number(item.material_id))
              ?? resolveMaterialLabel?.('video', item.material_id)
              ?? `视频 #${item.material_id}`,
            asset_excerpt: cleanText(item.role),
            source_label: '当前入选视频',
            sequence: item.sequence ?? index + 1,
            instance_no: item.instance_no ?? index + 1,
          },
          'defined',
        )),
  }

  const draftCandidates = draft?.candidateItems ?? creative.candidate_items ?? []
  const draftFreeCandidates = draftCandidates.filter((item) => item.source_kind !== 'product_derived')
  const draftProductCandidates = draftCandidates.filter((item) => item.source_kind === 'product_derived')

  const freeMaterialZone: CreativeFreeMaterialZoneResponse = {
    cover_candidates:
      creative.free_material_zone?.cover_candidates
      ?? draftFreeCandidates
        .filter((item) => item.candidate_type === 'cover')
        .map((item) => toDraftCandidate(item, false, currentCoverAssetId === item.asset_id, resolveMaterialLabel))
        .filter((item): item is CreativeZoneMaterialCandidateResponse => Boolean(item)),
    video_candidates:
      creative.free_material_zone?.video_candidates
      ?? draftFreeCandidates
        .filter((item) => item.candidate_type === 'video')
        .map((item) => toDraftCandidate(item, selectedVideoIds.has(Number(item.asset_id)), false, resolveMaterialLabel))
        .filter((item): item is CreativeZoneMaterialCandidateResponse => Boolean(item)),
    audio_candidates:
      creative.free_material_zone?.audio_candidates
      ?? draftFreeCandidates
        .filter((item) => item.candidate_type === 'audio')
        .map((item) => toDraftCandidate(item, selectedAudioIds.has(Number(item.asset_id)), false, resolveMaterialLabel))
        .filter((item): item is CreativeZoneMaterialCandidateResponse => Boolean(item)),
    copywriting_candidates:
      creative.free_material_zone?.copywriting_candidates
      ?? draftFreeCandidates
        .filter((item) => item.candidate_type === 'copywriting')
        .map((item) => toDraftCandidate(item, currentCopywritingId === item.asset_id, currentCopywritingId === item.asset_id, resolveMaterialLabel))
        .filter((item): item is CreativeZoneMaterialCandidateResponse => Boolean(item)),
  }

  const productZone: CreativeProductZoneResponse = {
    primary_product: creative.product_zone?.primary_product ?? (
      primaryProductLink
        ? {
          id: primaryProduct?.id ?? primaryProductLink.product_id,
          name: primaryProduct?.name ?? primaryProductLink.product_name ?? `商品 #${primaryProductLink.product_id}`,
          link_id: primaryProduct?.link_id ?? primaryProductLink.id ?? null,
          source_mode: primaryProduct?.source_mode ?? primaryProductLink.source_mode ?? null,
          is_primary: true,
          enabled: primaryProduct?.enabled ?? primaryProductLink.enabled ?? true,
          cover_count: primaryProduct?.cover_count,
          video_count: primaryProduct?.video_count,
          copywriting_count: primaryProduct?.copywriting_count,
        }
        : null
    ),
    linked_products: creative.product_zone?.linked_products ?? productLinks,
    product_name_candidate: creative.product_zone?.product_name_candidate ?? (
      primaryProductLink
        ? {
          product_id: primaryProductLink.product_id,
          product_name: primaryProductLink.product_name ?? currentProductName ?? `商品 #${primaryProductLink.product_id}`,
          is_selected: Boolean(currentProductName),
          is_detached: (draft?.productNameMode ?? creative.product_name_mode) === 'manual',
        }
        : null
    ),
    cover_candidates:
      creative.product_zone?.cover_candidates
      ?? draftProductCandidates
        .filter((item) => item.candidate_type === 'cover')
        .map((item) => toDraftCandidate(item, currentCoverAssetId === item.asset_id, currentCoverAssetId === item.asset_id, resolveMaterialLabel))
        .filter((item): item is CreativeZoneMaterialCandidateResponse => Boolean(item)),
    video_candidates:
      creative.product_zone?.video_candidates
      ?? draftProductCandidates
        .filter((item) => item.candidate_type === 'video')
        .map((item) => toDraftCandidate(item, selectedVideoIds.has(Number(item.asset_id)), false, resolveMaterialLabel))
        .filter((item): item is CreativeZoneMaterialCandidateResponse => Boolean(item)),
    copywriting_candidates:
      creative.product_zone?.copywriting_candidates
      ?? draftProductCandidates
        .filter((item) => item.candidate_type === 'copywriting')
        .map((item) => toDraftCandidate(item, currentCopywritingId === item.asset_id, currentCopywritingId === item.asset_id, resolveMaterialLabel))
        .filter((item): item is CreativeZoneMaterialCandidateResponse => Boolean(item)),
  }

  return {
    pageMode,
    readiness,
    currentSelection,
    productZone,
    freeMaterialZone,
  }
}
