import type {
  CreativeDetailResponse,
  CreativeInputItemResponse,
  CreativeInputItemWrite,
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
  target_duration_seconds: number | null
  input_items: Array<CreativeInputItemWrite>
} => ({
  title: values.title?.trim() ? values.title.trim() : undefined,
  profile_id: values.profile_id ?? null,
  subject_product_id: values.subject_product_id ?? null,
  subject_product_name_snapshot: values.subject_product_name_snapshot?.trim() || null,
  main_copywriting_text: values.main_copywriting_text?.trim() || null,
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
})

export const countEnabledCreativeInputItems = (
  items: Array<Pick<CreativeInputItemResponse, 'enabled'> | CreativeAuthoringInputItemFormValue> | undefined,
): number => (items ?? []).filter((item) => item.enabled !== false).length

export const formatCreativeDuration = (value?: number | null): string =>
  value && value > 0 ? `${value} 秒` : '未设定时长'
