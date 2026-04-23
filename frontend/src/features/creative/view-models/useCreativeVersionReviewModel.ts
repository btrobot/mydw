import { useCallback, useMemo, useState } from 'react'

import {
  creativeReviewConclusionMeta,
  type CreativeDetail,
  type CreativeVersionSummary,
} from '../types/creative'

type UseCreativeVersionReviewModelParams = {
  creative: CreativeDetail | undefined
  openAiClipWorkflow: () => void
}

export function useCreativeVersionReviewModel({
  creative,
  openAiClipWorkflow,
}: UseCreativeVersionReviewModelParams) {
  const [drawerOpen, setDrawerOpen] = useState(false)

  const currentVersion = creative?.versions?.find((version) => version.is_current) ?? null
  const currentVersionResult = creative?.current_version ?? null
  const versionById = useMemo(
    () => new Map((creative?.versions ?? []).map((version) => [version.id, version])),
    [creative?.versions],
  )
  const currentPackageRecord = currentVersionResult?.package_record ?? currentVersion?.package_record ?? null
  const effectiveCheck = creative?.review_summary?.current_check
  const effectiveCheckMeta = effectiveCheck ? creativeReviewConclusionMeta[effectiveCheck.conclusion] : null

  const openReviewDrawer = useCallback(() => {
    setDrawerOpen(true)
  }, [])

  const closeReviewDrawer = useCallback(() => {
    setDrawerOpen(false)
  }, [])

  const handleOpenAiClipVersion = useCallback((version: CreativeVersionSummary) => {
    if (version.is_current) {
      openAiClipWorkflow()
    }
  }, [openAiClipWorkflow])

  const handleReviewVersion = useCallback((version: CreativeVersionSummary) => {
    if (version.is_current) {
      setDrawerOpen(true)
    }
  }, [])

  return {
    currentVersion,
    currentVersionResult,
    versionById,
    currentPackageRecord,
    effectiveCheck,
    effectiveCheckMeta,
    reviewDrawerOpen: drawerOpen,
    openReviewDrawer,
    closeReviewDrawer,
    handleOpenAiClipVersion,
    handleReviewVersion,
  }
}

