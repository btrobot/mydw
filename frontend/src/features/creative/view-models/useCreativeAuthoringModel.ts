import { useCallback, useEffect, useMemo } from 'react'
import { Form } from 'antd'

import {
  buildCreativeAuthoringPayload,
  creativeCandidateMeta,
  countEnabledCreativeInputItems,
  creativeSelectedMediaMeta,
  getPrimaryCreativeProductId,
  toCreativeAuthoringFormValues,
  type CreativeAuthoringFormValues,
  type CreativeAuthoringCandidateType,
  type CreativeSelectedMediaType,
} from '../creativeAuthoring'
import {
  useSubmitCreativeComposition,
  useUpdateCreative,
} from '../hooks/useCreatives'
import type { CreativeDetail } from '../types/creative'
import { useAudios } from '@/hooks/useAudio'
import { useCopywritings } from '@/hooks/useCopywriting'
import { useCovers } from '@/hooks/useCover'
import { useProducts } from '@/hooks/useProduct'
import { useProfiles } from '@/hooks/useProfile'
import { useVideos } from '@/hooks/useVideo'

type MessageApi = {
  success: (content: string) => unknown
  error: (content: string) => unknown
}

type RefreshCallback = () => Promise<unknown>

type UseCreativeAuthoringModelParams = {
  creativeId: number | undefined
  creative: CreativeDetail | undefined
  hasCurrentVersion: boolean
  messageApi: MessageApi
  refreshCreative: RefreshCallback
  refreshDiagnostics: RefreshCallback
  onCompositionSubmitted: (taskId: number) => void
}

export function useCreativeAuthoringModel({
  creativeId,
  creative,
  hasCurrentVersion,
  messageApi,
  refreshCreative,
  refreshDiagnostics,
  onCompositionSubmitted,
}: UseCreativeAuthoringModelParams) {
  const [form] = Form.useForm<CreativeAuthoringFormValues>()
  const updateCreative = useUpdateCreative(creativeId)
  const submitCreativeComposition = useSubmitCreativeComposition(creativeId)
  const productsQuery = useProducts()
  const { data: profilesData } = useProfiles()
  const videosQuery = useVideos()
  const copywritingsQuery = useCopywritings()
  const coversQuery = useCovers()
  const audiosQuery = useAudios()

  const selectedProfileId = Form.useWatch('profile_id', form)
  const selectedProductLinks = Form.useWatch('product_links', form) ?? []
  const watchedCurrentProductName = Form.useWatch('current_product_name', form)
  const watchedTargetDuration = Form.useWatch('target_duration_seconds', form)
  const authoredInputItems = Form.useWatch('input_items', form) ?? []

  const profiles = profilesData?.items ?? []
  const products = productsQuery.data ?? []
  const videos = videosQuery.data ?? []
  const copywritings = copywritingsQuery.data ?? []
  const covers = coversQuery.data ?? []
  const audios = audiosQuery.data ?? []

  useEffect(() => {
    if (!creative) {
      return
    }
    form.setFieldsValue(toCreativeAuthoringFormValues(creative))
  }, [creative, form])

  const refetchAfterAuthoringCommit = useCallback(() => {
    void Promise.all([
      refreshCreative(),
      refreshDiagnostics(),
    ])
  }, [refreshCreative, refreshDiagnostics])

  const persistCreativeInput = useCallback(async (successMessage?: string) => {
    try {
      const values = await form.validateFields()
      await updateCreative.mutateAsync(buildCreativeAuthoringPayload(values))
      if (successMessage) {
        messageApi.success(successMessage)
      }
      refetchAfterAuthoringCommit()
      return true
    } catch (error: unknown) {
      if (error !== null && typeof error === 'object' && 'errorFields' in error) {
        return false
      }
      if (error instanceof Error) {
        messageApi.error(error.message)
      } else {
        messageApi.error('保存作品输入失败')
      }
      return false
    }
  }, [form, messageApi, refetchAfterAuthoringCommit, updateCreative])

  const handleSaveInput = useCallback(async () => {
    await persistCreativeInput('作品输入已保存')
  }, [persistCreativeInput])

  const handleSubmitComposition = useCallback(async () => {
    const saved = await persistCreativeInput()
    if (!saved) {
      return
    }

    try {
      const result = await submitCreativeComposition.mutateAsync()
      onCompositionSubmitted(result.task_id)

      const actionMessages: Record<string, string> = {
        created_and_submitted: `已提交合成任务 #${result.task_id}，当前作品会持续同步执行进度`,
        reused_draft_and_submitted: `已复用草稿任务 #${result.task_id} 并提交合成`,
        reused_composing: `已有进行中的合成任务 #${result.task_id}，已直接复用`,
        created_ready_task: `已生成直发版本，作品进入待审核（执行记录 #${result.task_id}）`,
        reused_ready_task: `已复用现有直发结果（执行记录 #${result.task_id}）`,
      }
      messageApi.success(actionMessages[result.submission_action] ?? `操作成功（任务 #${result.task_id}）`)
      refetchAfterAuthoringCommit()
    } catch (error: unknown) {
      if (error instanceof Error) {
        messageApi.error(error.message)
      } else {
        messageApi.error('提交作品合成失败')
      }
    }
  }, [
    messageApi,
    onCompositionSubmitted,
    persistCreativeInput,
    refetchAfterAuthoringCommit,
    submitCreativeComposition,
  ])

  const profileOptions = useMemo(
    () => profiles.map((profile) => ({
      value: profile.id,
      label: profile.is_default ? `${profile.name}（默认）` : profile.name,
    })),
    [profiles],
  )
  const productOptions = useMemo(
    () => products.map((product) => ({ value: product.id, label: product.name })),
    [products],
  )
  const productNameById = useMemo(
    () => new Map(products.map((product) => [product.id, product.name])),
    [products],
  )
  const coverNameById = useMemo(
    () => new Map(covers.map((item) => [item.id, item.name || `封面 #${item.id}`])),
    [covers],
  )
  const copywritingContentById = useMemo(
    () => new Map(copywritings.map((item) => [item.id, item.content || ''])),
    [copywritings],
  )
  const videoOptions = useMemo(
    () => videos.map((item) => ({ value: item.id, label: item.name || `视频 #${item.id}` })),
    [videos],
  )
  const copywritingOptions = useMemo(
    () => copywritings.map((item) => ({ value: item.id, label: item.name || `文案 #${item.id}` })),
    [copywritings],
  )
  const coverOptions = useMemo(
    () => covers.map((item) => ({ value: item.id, label: item.name || `封面 #${item.id}` })),
    [covers],
  )
  const audioOptions = useMemo(
    () => audios.map((item) => ({ value: item.id, label: item.name || `音频 #${item.id}` })),
    [audios],
  )
  const materialTypeOptions = useMemo(
    () => Object.entries(creativeSelectedMediaMeta).map(([value, meta]) => ({
      value,
      label: meta.label,
    })),
    [],
  )
  const candidateTypeOptions = useMemo(
    () => (Object.entries(creativeCandidateMeta) as Array<[CreativeAuthoringCandidateType, { label: string }]>)
      .map(([value, meta]) => ({
        value,
        label: meta.label,
      })),
    [],
  )
  const materialOptionsByType = useMemo<
    Record<CreativeAuthoringCandidateType | CreativeSelectedMediaType, Array<{ value: number; label: string }>>
  >(
    () => ({
      video: videoOptions,
      copywriting: copywritingOptions,
      cover: coverOptions,
      audio: audioOptions,
    }),
    [audioOptions, copywritingOptions, coverOptions, videoOptions],
  )
  const materialLoadingByType = useMemo<Record<CreativeAuthoringCandidateType | CreativeSelectedMediaType, boolean>>(
    () => ({
      video: videosQuery.isLoading,
      copywriting: copywritingsQuery.isLoading,
      cover: coversQuery.isLoading,
      audio: audiosQuery.isLoading,
    }),
    [
      audiosQuery.isLoading,
      copywritingsQuery.isLoading,
      coversQuery.isLoading,
      videosQuery.isLoading,
    ],
  )
  const canonicalProfileId = selectedProfileId ?? creative?.input_orchestration?.profile_id ?? undefined
  const activeProfile = useMemo(
    () => profiles.find((profile) => profile.id === canonicalProfileId),
    [canonicalProfileId, profiles],
  )
  const activeInputItemCount = countEnabledCreativeInputItems(authoredInputItems)
  const selectedSubjectProductId = getPrimaryCreativeProductId(selectedProductLinks)

  const getFormProductLinks = useCallback(
    (): CreativeAuthoringFormValues['product_links'] =>
      ((form.getFieldValue('product_links') as CreativeAuthoringFormValues['product_links'] | undefined) ?? []),
    [form],
  )
  const getFormCandidateItems = useCallback(
    (): CreativeAuthoringFormValues['candidate_items'] =>
      ((form.getFieldValue('candidate_items') as CreativeAuthoringFormValues['candidate_items'] | undefined) ?? []),
    [form],
  )
  const getFormInputItems = useCallback(
    (): CreativeAuthoringFormValues['input_items'] =>
      ((form.getFieldValue('input_items') as CreativeAuthoringFormValues['input_items'] | undefined) ?? []),
    [form],
  )
  const clearCandidateAdoptionStatus = useCallback((candidateType: CreativeAuthoringCandidateType) => {
    const candidateItems = [...getFormCandidateItems()]
    const nextCandidateItems = candidateItems.map((item) => (
      item.candidate_type === candidateType && item.status === 'adopted'
        ? { ...item, status: 'candidate' as const }
        : item
    ))
    form.setFieldValue('candidate_items', nextCandidateItems)
  }, [form, getFormCandidateItems])
  const syncCurrentTruthFromCandidate = useCallback((candidateType: CreativeAuthoringCandidateType, assetId?: number) => {
    if (!assetId) {
      return
    }
    if (candidateType === 'cover') {
      form.setFieldValue('current_cover_asset_id', assetId)
      form.setFieldValue('current_cover_asset_type', 'cover')
      form.setFieldValue('cover_mode', 'adopted_candidate')
      return
    }
    if (candidateType === 'copywriting') {
      form.setFieldValue('current_copywriting_id', assetId)
      form.setFieldValue('current_copywriting_text', copywritingContentById.get(assetId) ?? '')
      form.setFieldValue('copywriting_mode', 'adopted_candidate')
    }
  }, [copywritingContentById, form])
  const syncCurrentProductNameFromPrimary = useCallback((productId?: number) => {
    const currentMode = form.getFieldValue('product_name_mode') as string | undefined
    if (currentMode === 'manual') {
      return
    }
    if (!productId) {
      form.setFieldValue(
        'product_name_mode',
        (form.getFieldValue('current_product_name') as string | undefined)?.trim() ? 'manual' : undefined,
      )
      return
    }
    const nextName = productNameById.get(productId)
    if (nextName) {
      form.setFieldValue('current_product_name', nextName)
      form.setFieldValue('product_name_mode', 'follow_primary_product')
    }
  }, [form, productNameById])
  const handleMakePrimaryProductLink = useCallback((index: number) => {
    const productLinks = [...getFormProductLinks()]
    if (!productLinks[index]) {
      return
    }
    const nextProductLinks = productLinks.map((item, currentIndex) => ({
      ...item,
      is_primary: currentIndex === index,
    }))
    form.setFieldValue('product_links', nextProductLinks)
    syncCurrentProductNameFromPrimary(nextProductLinks[index]?.product_id)
  }, [form, getFormProductLinks, syncCurrentProductNameFromPrimary])
  const handleProductLinkProductChange = useCallback((index: number, productId?: number) => {
    const productLinks = [...getFormProductLinks()]
    const currentLink = productLinks[index]
    if (!currentLink) {
      return
    }
    const isPrimary = Boolean(currentLink.is_primary)
      || !productLinks.some((item, currentIndex) => currentIndex !== index && item.is_primary)
    const nextProductLinks = productLinks.map((item, currentIndex) => ({
      ...item,
      is_primary: currentIndex === index ? isPrimary : (isPrimary ? false : Boolean(item.is_primary)),
    }))
    nextProductLinks[index] = {
      ...nextProductLinks[index],
      product_id: productId,
      enabled: nextProductLinks[index]?.enabled ?? true,
      source_mode: nextProductLinks[index]?.source_mode ?? 'manual_add',
    }
    form.setFieldValue('product_links', nextProductLinks)
    if (isPrimary) {
      syncCurrentProductNameFromPrimary(productId)
    }
  }, [form, getFormProductLinks, syncCurrentProductNameFromPrimary])
  const handleCandidateItemTypeChange = useCallback((index: number, candidateType?: CreativeAuthoringCandidateType) => {
    const candidateItems = [...getFormCandidateItems()]
    const currentItem = candidateItems[index]
    if (!currentItem) {
      return
    }
    candidateItems[index] = {
      ...currentItem,
      candidate_type: candidateType,
      asset_id: undefined,
      status: 'candidate',
      source_kind: currentItem.source_kind ?? 'material_library',
    }
    form.setFieldValue('candidate_items', candidateItems)
  }, [form, getFormCandidateItems])
  const handleCandidateItemAssetChange = useCallback((index: number, assetId?: number) => {
    const candidateItems = [...getFormCandidateItems()]
    const currentItem = candidateItems[index]
    if (!currentItem) {
      return
    }
    candidateItems[index] = {
      ...currentItem,
      asset_id: assetId,
      source_kind: currentItem.source_kind ?? 'material_library',
      status: currentItem.status ?? 'candidate',
      enabled: currentItem.enabled ?? true,
    }
    form.setFieldValue('candidate_items', candidateItems)
    if (currentItem.status === 'adopted' && currentItem.candidate_type) {
      syncCurrentTruthFromCandidate(currentItem.candidate_type, assetId)
    }
  }, [form, getFormCandidateItems, syncCurrentTruthFromCandidate])
  const handleAdoptCandidateItem = useCallback((index: number) => {
    const candidateItems = [...getFormCandidateItems()]
    const currentItem = candidateItems[index]
    if (!currentItem?.candidate_type || !currentItem.asset_id) {
      return
    }
    const nextCandidateItems = candidateItems.map((item, currentIndex) => {
      if (item.candidate_type !== currentItem.candidate_type) {
        return item
      }
      return {
        ...item,
        status: currentIndex === index ? 'adopted' : (item.status === 'dismissed' ? 'dismissed' : 'candidate'),
      }
    })
    form.setFieldValue('candidate_items', nextCandidateItems)
    syncCurrentTruthFromCandidate(currentItem.candidate_type, currentItem.asset_id)
  }, [form, getFormCandidateItems, syncCurrentTruthFromCandidate])
  const handleCurrentProductNameChange = useCallback((value: string) => {
    const selectedProductName = selectedSubjectProductId ? productNameById.get(selectedSubjectProductId) : undefined
    if (selectedProductName && value.trim() === selectedProductName) {
      form.setFieldValue('product_name_mode', 'follow_primary_product')
      return
    }
    form.setFieldValue('product_name_mode', value.trim() ? 'manual' : undefined)
  }, [form, productNameById, selectedSubjectProductId])
  const handleCurrentCopywritingTextChange = useCallback((value: string) => {
    form.setFieldValue('current_copywriting_id', null)
    form.setFieldValue('copywriting_mode', value.trim() ? 'manual' : undefined)
    clearCandidateAdoptionStatus('copywriting')
  }, [clearCandidateAdoptionStatus, form])
  const handleSetPrimaryProduct = useCallback((productId: number) => {
    const productLinks = [...getFormProductLinks()]
    const existingIndex = productLinks.findIndex((item) => item.product_id === productId)

    if (existingIndex >= 0) {
      const nextProductLinks = productLinks.map((item, index) => ({
        ...item,
        is_primary: index === existingIndex,
        enabled: item.enabled ?? true,
        source_mode: item.source_mode ?? 'manual_add',
      }))
      form.setFieldValue('product_links', nextProductLinks)
      syncCurrentProductNameFromPrimary(productId)
      return
    }

    const nextProductLinks = [
      ...productLinks.map((item) => ({
        ...item,
        is_primary: false,
        enabled: item.enabled ?? true,
        source_mode: item.source_mode ?? 'manual_add',
      })),
      {
        product_id: productId,
        is_primary: true,
        enabled: true,
        source_mode: 'manual_add' as const,
      },
    ]
    form.setFieldValue('product_links', nextProductLinks)
    syncCurrentProductNameFromPrimary(productId)
  }, [form, getFormProductLinks, syncCurrentProductNameFromPrimary])
  const handleUseProductNameCandidate = useCallback((productId: number, productName: string) => {
    form.setFieldValue('current_product_name', productName)
    form.setFieldValue('product_name_mode', 'follow_primary_product')
    const productLinks = [...getFormProductLinks()]
    const existingIndex = productLinks.findIndex((item) => item.product_id === productId)
    if (existingIndex >= 0) {
      const nextProductLinks = productLinks.map((item, index) => ({
        ...item,
        is_primary: index === existingIndex,
        enabled: item.enabled ?? true,
        source_mode: item.source_mode ?? 'manual_add',
      }))
      form.setFieldValue('product_links', nextProductLinks)
      return
    }
    handleSetPrimaryProduct(productId)
  }, [form, getFormProductLinks, handleSetPrimaryProduct])
  const handleRestorePrimaryProductName = useCallback(() => {
    syncCurrentProductNameFromPrimary(selectedSubjectProductId)
  }, [selectedSubjectProductId, syncCurrentProductNameFromPrimary])
  const handleSetCurrentCover = useCallback((assetId?: number, assetType: 'cover' = 'cover') => {
    form.setFieldValue('current_cover_asset_id', assetId ?? null)
    form.setFieldValue('current_cover_asset_type', assetId ? assetType : null)
    form.setFieldValue('cover_mode', assetId ? 'manual' : null)
    if (!assetId) {
      clearCandidateAdoptionStatus('cover')
    }
  }, [clearCandidateAdoptionStatus, form])
  const handleSetCurrentCopywriting = useCallback((assetId?: number, text?: string) => {
    form.setFieldValue('current_copywriting_id', assetId ?? null)
    form.setFieldValue('current_copywriting_text', text ?? '')
    form.setFieldValue('copywriting_mode', assetId ? 'manual' : null)
    if (!assetId) {
      clearCandidateAdoptionStatus('copywriting')
    }
  }, [clearCandidateAdoptionStatus, form])
  const handleSetCurrentAudio = useCallback((assetId?: number) => {
    const existingItems = [...getFormInputItems()]
    const nonAudioItems = existingItems.filter((item) => item.material_type !== 'audio')
    const nextItems = assetId
      ? [
        ...nonAudioItems,
        {
          material_type: 'audio' as const,
          material_id: assetId,
          enabled: true,
        },
      ]
      : nonAudioItems
    form.setFieldValue('input_items', nextItems)
  }, [form, getFormInputItems])
  const handleToggleSelectedVideo = useCallback((assetId: number) => {
    const existingItems = [...getFormInputItems()]
    const hasSelectedVideo = existingItems.some((item) => (
      item.material_type === 'video' && item.material_id === assetId && item.enabled !== false
    ))
    const nextItems = hasSelectedVideo
      ? existingItems.filter((item) => !(item.material_type === 'video' && item.material_id === assetId))
      : [
        ...existingItems,
        {
          material_type: 'video' as const,
          material_id: assetId,
          enabled: true,
        },
      ]
    form.setFieldValue('input_items', nextItems)
  }, [form, getFormInputItems])
  const handleRemoveSelectedVideo = useCallback((assetId?: number) => {
    if (!assetId) {
      return
    }
    const existingItems = [...getFormInputItems()]
    form.setFieldValue(
      'input_items',
      existingItems.filter((item) => !(item.material_type === 'video' && item.material_id === assetId)),
    )
  }, [form, getFormInputItems])
  const handleMoveSelectedVideo = useCallback((videoIndex: number, direction: 'up' | 'down') => {
    const existingItems = [...getFormInputItems()]
    const videoSlotIndexes = existingItems
      .map((item, index) => (item.material_type === 'video' ? index : -1))
      .filter((index) => index >= 0)

    const targetIndex = direction === 'up' ? videoIndex - 1 : videoIndex + 1
    if (
      videoIndex < 0
      || videoIndex >= videoSlotIndexes.length
      || targetIndex < 0
      || targetIndex >= videoSlotIndexes.length
    ) {
      return
    }

    const nextItems = [...existingItems]
    const currentSlot = videoSlotIndexes[videoIndex]
    const targetSlot = videoSlotIndexes[targetIndex]
    const currentVideo = nextItems[currentSlot]
    nextItems[currentSlot] = nextItems[targetSlot]
    nextItems[targetSlot] = currentVideo
    form.setFieldValue('input_items', nextItems)
  }, [form, getFormInputItems])
  const handleUpdateSelectedVideoRole = useCallback((videoIndex: number, role: string) => {
    const existingItems = [...getFormInputItems()]
    const videoSlotIndexes = existingItems
      .map((item, index) => (item.material_type === 'video' ? index : -1))
      .filter((index) => index >= 0)
    const targetSlot = videoSlotIndexes[videoIndex]
    if (targetSlot === undefined) {
      return
    }

    const nextItems = [...existingItems]
    nextItems[targetSlot] = {
      ...nextItems[targetSlot],
      role,
    }
    form.setFieldValue('input_items', nextItems)
  }, [form, getFormInputItems])
  const submitButtonLabel = activeProfile?.composition_mode === 'none'
    ? '提交直发准备'
    : (hasCurrentVersion ? '重新提交合成' : '提交合成')

  return {
    form,
    updateCreative,
    submitCreativeComposition,
    productsQuery,
    watchedCurrentProductName,
    watchedTargetDuration,
    profileOptions,
    productOptions,
    coverNameById,
    candidateTypeOptions,
    materialTypeOptions,
    materialOptionsByType,
    materialLoadingByType,
    canonicalProfileId,
    activeProfile,
    activeInputItemCount,
    handleMakePrimaryProductLink,
    handleAdoptCandidateItem,
    handleCandidateItemAssetChange,
    handleCandidateItemTypeChange,
    handleProductLinkProductChange,
    handleCurrentProductNameChange,
    handleCurrentCopywritingTextChange,
    handleSetPrimaryProduct,
    handleUseProductNameCandidate,
    handleRestorePrimaryProductName,
    handleSetCurrentCover,
    handleSetCurrentCopywriting,
    handleSetCurrentAudio,
    handleToggleSelectedVideo,
    handleRemoveSelectedVideo,
    handleMoveSelectedVideo,
    handleUpdateSelectedVideoRole,
    handleSaveInput,
    handleSubmitComposition,
    submitButtonLabel,
  }
}

