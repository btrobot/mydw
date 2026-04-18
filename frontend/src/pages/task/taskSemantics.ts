import type { TaskResponse } from '@/api'
import type { CompositionMode, PublishProfileResponse } from '@/hooks/useProfile'

export type EffectiveCompositionMode = CompositionMode

export interface TaskMaterialCounts {
  videos: number
  copywritings: number
  covers: number
  audios: number
  topics: number
}

export interface TaskSemanticsSummary {
  mode: EffectiveCompositionMode
  modeLabel: string
  counts: TaskMaterialCounts
  directPublishAllowed: boolean
  violations: string[]
  usesFinalVideo: boolean
}

const MODE_LABELS: Record<EffectiveCompositionMode, string> = {
  none: '直接发布',
  coze: 'Coze 合成',
  local_ffmpeg: '本地 FFmpeg 合成',
}

export function resolveCompositionMode(
  profileId: number | null | undefined,
  profiles: PublishProfileResponse[],
): EffectiveCompositionMode {
  if (profileId) {
    const selected = profiles.find((profile) => profile.id === profileId)
    if (selected) return selected.composition_mode
  }
  return profiles.find((profile) => profile.is_default)?.composition_mode ?? 'none'
}

export function getTaskMaterialCounts(task: Pick<TaskResponse, 'video_ids' | 'copywriting_ids' | 'cover_ids' | 'audio_ids' | 'topic_ids'>): TaskMaterialCounts {
  return {
    videos: task.video_ids?.length ?? 0,
    copywritings: task.copywriting_ids?.length ?? 0,
    covers: task.cover_ids?.length ?? 0,
    audios: task.audio_ids?.length ?? 0,
    topics: task.topic_ids?.length ?? 0,
  }
}

export function getDirectPublishViolations(
  counts: TaskMaterialCounts,
  options?: { usesFinalVideo?: boolean },
): string[] {
  const violations: string[] = []
  const usesFinalVideo = options?.usesFinalVideo ?? false

  if (!usesFinalVideo && counts.videos !== 1) {
    violations.push(`直接发布仅支持 1 个最终视频，当前有 ${counts.videos} 个视频`)
  }
  if (counts.copywritings > 1) {
    violations.push(`直接发布仅支持 0 或 1 个文案，当前有 ${counts.copywritings} 个文案`)
  }
  if (counts.covers > 1) {
    violations.push(`直接发布仅支持 0 或 1 个封面，当前有 ${counts.covers} 个封面`)
  }
  if (!usesFinalVideo && counts.audios > 0) {
    violations.push('直接发布不支持独立音频输入，请先走合成流程')
  }

  return violations
}

export function getTaskSemanticsSummary(
  task: Pick<TaskResponse, 'profile_id' | 'video_ids' | 'copywriting_ids' | 'cover_ids' | 'audio_ids' | 'topic_ids' | 'final_video_path'>,
  profiles: PublishProfileResponse[],
): TaskSemanticsSummary {
  const mode = resolveCompositionMode(task.profile_id, profiles)
  const counts = getTaskMaterialCounts(task)
  const usesFinalVideo = Boolean(task.final_video_path)

  if (mode !== 'none') {
    return {
      mode,
      modeLabel: MODE_LABELS[mode],
      counts,
      directPublishAllowed: usesFinalVideo,
      violations: usesFinalVideo ? [] : ['当前任务为合成模式，需先完成合成后再进入直接发布语义'],
      usesFinalVideo,
    }
  }

  return {
    mode,
    modeLabel: MODE_LABELS[mode],
    counts,
    directPublishAllowed: usesFinalVideo && counts.copywritings <= 1 && counts.covers <= 1,
    violations: getDirectPublishViolations(counts, { usesFinalVideo }),
    usesFinalVideo,
  }
}
