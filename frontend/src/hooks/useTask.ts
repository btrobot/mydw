/**
 * Task Hooks - 任务相关的 React Query hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listTasksApiTasksGet,
  createTaskApiTasksPost,
  getTaskApiTasksTaskIdGet,
  updateTaskApiTasksTaskIdPut,
  deleteTaskApiTasksTaskIdDelete,
  publishTaskApiTasksTaskIdPublishPost,
  batchCreateTasksApiTasksBatchPost,
  shuffleTasksApiTasksShufflePost,
  deleteAllTasksApiTasksDelete,
  getTaskStatsApiTasksStatsGet,
} from '@/api'

import type {
  TaskResponse,
  TaskStatsResponse,
  TaskListResponse,
  TaskCreate,
  TaskUpdate,
  TaskBatchCreateRequest,
} from '@/api'

export const useTasks = () =>
  useQuery<TaskListResponse>({
    queryKey: ['tasks'],
    queryFn: async () => {
      const response = await listTasksApiTasksGet()
      return response.data ?? { total: 0, items: [] }
    },
  })

export const useTask = (taskId: number) =>
  useQuery<TaskResponse>({
    queryKey: ['task', taskId],
    queryFn: async () => {
      const response = await getTaskApiTasksTaskIdGet({ path: { task_id: taskId } })
      return response.data!
    },
    enabled: !!taskId,
  })

export const useCreateTask = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: TaskCreate) => {
      const response = await createTaskApiTasksPost({ body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}

export const useUpdateTask = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ taskId, data }: { taskId: number; data: TaskUpdate }) => {
      const response = await updateTaskApiTasksTaskIdPut({ path: { task_id: taskId }, body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}

export const useDeleteTask = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (taskId: number) => {
      await deleteTaskApiTasksTaskIdDelete({ path: { task_id: taskId } })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}

export const usePublishTask = () =>
  useMutation({
    mutationFn: async (taskId: number) => {
      const response = await publishTaskApiTasksTaskIdPublishPost({ path: { task_id: taskId } })
      return response.data
    },
  })

export const useBatchCreateTasks = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: TaskBatchCreateRequest) => {
      const response = await batchCreateTasksApiTasksBatchPost({ body: data })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}

export const useShuffleTasks = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const response = await shuffleTasksApiTasksShufflePost()
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}

export const useDeleteAllTasks = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      await deleteAllTasksApiTasksDelete()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}

export const useTaskStats = () =>
  useQuery<TaskStatsResponse>({
    queryKey: ['taskStats'],
    queryFn: async () => {
      const response = await getTaskStatsApiTasksStatsGet()
      return response.data!
    },
  })

export const useAssembleTasks = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: {
      video_ids: number[]
      account_ids: number[]
      strategy?: string
      copywriting_mode?: string
    }) => {
      const { api } = await import('@/services/api')
      const { data: result } = await api.post<TaskResponse[]>('/tasks/assemble', data)
      return result
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })
}
