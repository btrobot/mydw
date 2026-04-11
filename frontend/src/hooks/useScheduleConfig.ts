/**
 * Schedule Config Hooks - canonical 调度配置 hooks
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getScheduleConfigApiScheduleConfigGet,
  updateScheduleConfigApiScheduleConfigPut,
} from '@/api'

import type {
  ScheduleConfigRequest,
  ScheduleConfigResponse,
} from '@/api'

export const SCHEDULE_CONFIG_QUERY_KEY = ['scheduleConfig'] as const

export const useScheduleConfig = () =>
  useQuery<ScheduleConfigResponse>({
    queryKey: SCHEDULE_CONFIG_QUERY_KEY,
    queryFn: async () => {
      const response = await getScheduleConfigApiScheduleConfigGet()
      return response.data!
    },
  })

export const useUpdateScheduleConfig = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: ScheduleConfigRequest) => {
      const response = await updateScheduleConfigApiScheduleConfigPut({ body: data })
      return response.data!
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SCHEDULE_CONFIG_QUERY_KEY })
    },
  })
}
