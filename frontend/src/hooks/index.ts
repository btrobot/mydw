/**
 * Hooks Index - 统一导出所有 API hooks
 *
 * 使用方式：
 * ```tsx
 * import { useAccounts, useTasks, QueryProvider } from '@/hooks'
 * ```
 */

// Re-export QueryProvider from provider
export { QueryProvider } from '@/providers/QueryProvider'

// Account Hooks
export {
  useAccounts,
  useAccount,
  useCreateAccount,
  useUpdateAccount,
  useDeleteAccount,
  useAccountStats,
  useLoginAccount,
  useTestAccount,
  usePreviewAccount,
  useClosePreview,
  usePreviewStatus,
  useHealthCheck,
  useBatchHealthCheck,
  useBatchCheckStatus,
} from './useAccount'
export type { PreviewStatus, HealthCheckResult, BatchHealthCheckResult, BatchHealthCheckProgress } from './useAccount'

// Task Hooks
export {
  useTasks,
  useTask,
  useCreateTask,
  useUpdateTask,
  useDeleteTask,
  usePublishTask,
  useBatchCreateTasks,
  useShuffleTasks,
  useDeleteAllTasks,
  useInitTasksFromMaterials,
  useAutoGenerateTasks,
  useTaskStats,
} from './useTask'

// Material Hooks
export {
  useMaterials,
  useMaterial,
  useCreateMaterial,
  useUpdateMaterial,
  useDeleteMaterial,
  useScanMaterials,
  useImportMaterials,
  useDeleteAllMaterials,
  useMaterialStats,
  useProducts,
  useCreateProduct,
  useDeleteProduct,
} from './useMaterial'

// Publish Hooks
export {
  usePublishConfig,
  useUpdatePublishConfig,
  useControlPublish,
  usePublishStatus,
  usePublishLogs,
} from './usePublish'

// System Hooks
export {
  useSystemStats,
  useSystemLogs,
  useBackup,
  useSystemConfig,
  useUpdateSystemConfig,
} from './useSystem'

// AI Clip Hooks
export {
  useVideoInfo,
  useDetectHighlights,
  useSmartClip,
  useTrimVideo,
  useAddAudio,
  useAddCover,
  useFullPipeline,
} from './useAIClip'

// Product Hooks (new domain API)
export { useProducts as useProductsV2, useCreateProduct as useCreateProductV2, useDeleteProduct as useDeleteProductV2 } from './useProduct'

// Video Hooks
export { useVideos, useCreateVideo, useDeleteVideo } from './useVideo'

// Copywriting Hooks
export { useCopywritings, useCreateCopywriting, useDeleteCopywriting } from './useCopywriting'

// Cover Hooks
export { useCovers, useUploadCover, useDeleteCover } from './useCover'

// Audio Hooks
export { useAudios, useUploadAudio, useDeleteAudio } from './useAudio'

// Topic Hooks
export { useTopics, useCreateTopic, useDeleteTopic } from './useTopic'
