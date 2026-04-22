/**
 * System Hooks - 系统相关的 React Query hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getSystemStatsApiSystemStatsGet,
  getSystemLogsApiSystemLogsGet,
  backupDataApiSystemBackupPost,
  getSystemConfigApiSystemConfigGet,
  updateSystemConfigApiSystemConfigPut,
} from '@/api'

import type {
  BackupResponse,
  SystemStats,
  BackupRequest,
  SystemLogListResponse,
  SystemConfigResponse,
  SystemConfigUpdateResponse,
} from '@/api'

export const useSystemStats = () =>
  useQuery<SystemStats>({
    queryKey: ['systemStats'],
    queryFn: async () => {
      const response = await getSystemStatsApiSystemStatsGet({
        throwOnError: true,
      })
      return response.data!
    },
    retry: false,
  })

export const useSystemLogs = () =>
  useQuery<SystemLogListResponse>({
    queryKey: ['systemLogs'],
    queryFn: async () => {
      const response = await getSystemLogsApiSystemLogsGet({
        throwOnError: true,
      })
      const data = response.data

      if (!data || !('items' in data)) {
        throw new Error('系统日志返回格式不合法')
      }

      return data as SystemLogListResponse
    },
    retry: false,
  })

export const useBackup = () =>
  useMutation({
    mutationFn: async (data: BackupRequest) => {
      const response = await backupDataApiSystemBackupPost({ body: data })
      return response.data as BackupResponse
    },
  })

export const useSystemConfig = () =>
  useQuery<SystemConfigResponse>({
    queryKey: ['systemConfig'],
    queryFn: async () => {
      const response = await getSystemConfigApiSystemConfigGet({
        throwOnError: true,
      })
      return response.data as SystemConfigResponse
    },
    retry: false,
  })

export const useUpdateSystemConfig = () => {
  const queryClient = useQueryClient()
  return useMutation<
    SystemConfigUpdateResponse | undefined,
    Error,
    {
      material_base_path?: string
      creative_flow_mode?: SystemConfigResponse['creative_flow_mode']
      creative_flow_shadow_compare?: boolean
    }
  >({
    mutationFn: async (data) => {
      const response = await updateSystemConfigApiSystemConfigPut({
        query: {
          material_base_path: data.material_base_path,
          creative_flow_mode: data.creative_flow_mode,
          creative_flow_shadow_compare: data.creative_flow_shadow_compare,
        },
      })
      return response.data as SystemConfigUpdateResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systemConfig'] })
    },
  })
}
