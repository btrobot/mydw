/**
 * System Hooks - 系统相关的 React Query hooks
 */
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  getSystemStatsApiSystemStatsGet,
  getSystemLogsApiSystemLogsGet,
  backupDataApiSystemBackupPost,
  getSystemConfigApiSystemConfigGet,
  updateSystemConfigApiSystemConfigPut,
} from '@/api'

import type {
  SystemStats,
  BackupRequest,
  SystemLogListResponse,
} from '@/api'

export const useSystemStats = () =>
  useQuery<SystemStats>({
    queryKey: ['systemStats'],
    queryFn: async () => {
      const response = await getSystemStatsApiSystemStatsGet()
      return response.data!
    },
  })

export const useSystemLogs = () =>
  useQuery<SystemLogListResponse>({
    queryKey: ['systemLogs'],
    queryFn: async () => {
      const response = await getSystemLogsApiSystemLogsGet()
      const data = response.data
      if (data && 'items' in data) return data as SystemLogListResponse
      return { total: 0, items: [] }
    },
  })

export const useBackup = () =>
  useMutation({
    mutationFn: async (data: BackupRequest) => {
      const response = await backupDataApiSystemBackupPost({ body: data })
      return response.data
    },
  })

export const useSystemConfig = () =>
  useQuery({
    queryKey: ['systemConfig'],
    queryFn: async () => {
      const response = await getSystemConfigApiSystemConfigGet()
      return response.data
    },
  })

export const useUpdateSystemConfig = () =>
  useMutation({
    mutationFn: async (data: { material_base_path?: string; video_output_path?: string; log_level?: string }) => {
      await updateSystemConfigApiSystemConfigPut({ query: data })
    },
  })
