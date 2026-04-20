/**
 * Task Hooks - 任务相关的 React Query hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import {
  listTasksApiTasksGet,
  createTasksApiTasksPost,
  getTaskApiTasksTaskIdGet,
  updateTaskApiTasksTaskIdPut,
  deleteTaskApiTasksTaskIdDelete,
  publishTaskApiTasksTaskIdPublishPost,
  batchCreateTasksApiTasksBatchPost,
  shuffleTasksApiTasksShufflePost,
  deleteAllTasksApiTasksDelete,
  getTaskStatsApiTasksStatsGet,
  quickRetryTaskApiTasksTaskIdRetryPost,
  editRetryTaskApiTasksTaskIdEditRetryPost,
  cancelTaskApiTasksTaskIdCancelPost,
  submitCompositionApiTasksTaskIdSubmitCompositionPost,
  batchSubmitCompositionApiTasksBatchSubmitCompositionPost,
  getCompositionStatusApiTasksTaskIdCompositionStatusGet,
  cancelCompositionApiTasksTaskIdCancelCompositionPost,
} from '@/api'

import type {
  TaskResponse,
  TaskStatsResponse,
  TaskListResponse,
  TaskCreateRequest,
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
    mutationFn: async (data: TaskCreateRequest) => {
      const response = await createTasksApiTasksPost({ body: data })
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
      await deleteTaskApiTasksTaskIdDelete({
        path: { task_id: taskId },
        throwOnError: true,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}

export const usePublishTask = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (taskId: number) => {
      const response = await publishTaskApiTasksTaskIdPublishPost({ path: { task_id: taskId } })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}

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
      await deleteAllTasksApiTasksDelete({ throwOnError: true })
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

export const useRetryTask = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (taskId: number) => {
      const response = await quickRetryTaskApiTasksTaskIdRetryPost({ path: { task_id: taskId } })
      return response.data!
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })
}

export const useEditRetryTask = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (taskId: number) => {
      const response = await editRetryTaskApiTasksTaskIdEditRetryPost({ path: { task_id: taskId } })
      return response.data!
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })
}

export const useCancelTask = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (taskId: number) => {
      const response = await cancelTaskApiTasksTaskIdCancelPost({ path: { task_id: taskId } })
      return response.data!
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })
}

// ============ 合成 Hooks (FE-TM-04) ============

export interface CompositionJobResponse {
  id: number
  task_id: number
  workflow_type: string | null
  workflow_id: string | null
  external_job_id: string | null
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  output_video_path: string | null
  output_video_url: string | null
  error_msg: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface BatchSubmitCompositionResult {
  success_count: number
  failed_count: number
  results: Array<{
    task_id: number
    status: 'submitted' | 'failed'
    job_id?: number
    error?: string
  }>
}

export const useSubmitComposition = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (taskId: number) => {
      const response = await submitCompositionApiTasksTaskIdSubmitCompositionPost({
        path: { task_id: taskId },
      })
      return response.data as CompositionJobResponse
    },
    onSuccess: (_data, taskId) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      queryClient.invalidateQueries({ queryKey: ['compositionStatus', taskId] })
    },
  })
}

export const useBatchSubmitComposition = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (taskIds: number[]) => {
      const response = await batchSubmitCompositionApiTasksBatchSubmitCompositionPost({
        body: { task_ids: taskIds },
      })
      return response.data as unknown as BatchSubmitCompositionResult
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      queryClient.invalidateQueries({ queryKey: ['compositionStatus'] })
    },
  })
}

export const useCompositionStatus = (taskId: number | null) => {
  const queryClient = useQueryClient()
  const query = useQuery<CompositionJobResponse>({
    queryKey: ['compositionStatus', taskId],
    queryFn: async () => {
      const response = await getCompositionStatusApiTasksTaskIdCompositionStatusGet({
        path: { task_id: taskId! },
      })
      return response.data as CompositionJobResponse
    },
    enabled: taskId !== null,
    refetchInterval: false,
  })

  const isComposing = query.data?.status === 'pending' || query.data?.status === 'processing'
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (taskId === null) return
    if (isComposing) {
      intervalRef.current = setInterval(() => {
        void queryClient.invalidateQueries({ queryKey: ['compositionStatus', taskId] })
      }, 5000)
    } else {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [isComposing, taskId, queryClient])

  return query
}

export const useCancelComposition = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (taskId: number) => {
      const response = await cancelCompositionApiTasksTaskIdCancelCompositionPost({
        path: { task_id: taskId },
      })
      return response.data as CompositionJobResponse
    },
    onSuccess: (_data, taskId) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      queryClient.invalidateQueries({ queryKey: ['compositionStatus', taskId] })
    },
  })
}

// ============ Create Tasks (Resource Collection Model) ============

export interface CreateTasksRequest {
  video_ids: number[]
  copywriting_ids: number[]
  cover_ids: number[]
  audio_ids: number[]
  topic_ids: number[]
  account_ids: number[]
  profile_id?: number | null
  name?: string | null
}

export const useBatchAssemble = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: CreateTasksRequest) => {
      const response = await createTasksApiTasksPost({ body: data })
      return response.data ?? []
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })
}
