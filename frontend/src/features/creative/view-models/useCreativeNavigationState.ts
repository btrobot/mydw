import { useCallback, useMemo } from 'react'
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'

type CreativeDetailDiagnosticsView = 'advanced'

export function useCreativeNavigationState() {
  const location = useLocation()
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const [searchParams, setSearchParams] = useSearchParams()

  const creativeId = id ? Number.parseInt(id, 10) : undefined
  const requestedTaskId = Number.parseInt(searchParams.get('taskId') ?? '', 10)
  const prioritizedTaskId = Number.isFinite(requestedTaskId) ? requestedTaskId : undefined
  const detailCurrentRoute = useMemo(() => {
    const currentPath = `${location.pathname}${location.search}`
    return currentPath || (creativeId ? `/creative/${creativeId}` : '/creative/workbench')
  }, [creativeId, location.pathname, location.search])
  const detailReturnTo = searchParams.get('returnTo') || '/creative/workbench'
  const taskReturnTo = searchParams.get('returnTo') || detailCurrentRoute
  const detailDiagnosticsOpen = searchParams.get('diagnostics') === 'advanced'
  const aiClipRequested = searchParams.get('tool') === 'ai-clip'

  const openAiClipWorkflow = useCallback(() => {
    const nextParams = new URLSearchParams(searchParams)
    nextParams.set('tool', 'ai-clip')
    setSearchParams(nextParams, { replace: true })
  }, [searchParams, setSearchParams])

  const closeAiClipWorkflow = useCallback(() => {
    const nextParams = new URLSearchParams(searchParams)
    nextParams.delete('tool')
    setSearchParams(nextParams, { replace: true })
  }, [searchParams, setSearchParams])

  const setDiagnosticsView = useCallback((diagnostics?: CreativeDetailDiagnosticsView) => {
    const nextParams = new URLSearchParams(searchParams)
    if (diagnostics) {
      nextParams.set('diagnostics', diagnostics)
    } else {
      nextParams.delete('diagnostics')
    }
    setSearchParams(nextParams, { replace: true })
  }, [searchParams, setSearchParams])

  const handleOpenDiagnostics = useCallback(() => {
    setDiagnosticsView('advanced')
  }, [setDiagnosticsView])

  const handleCloseDiagnostics = useCallback(() => {
    setDiagnosticsView(undefined)
  }, [setDiagnosticsView])

  const openTaskDiagnostics = useCallback((taskId: number) => {
    const params = new URLSearchParams({ returnTo: taskReturnTo })
    navigate(`/task/${taskId}?${params.toString()}`)
  }, [navigate, taskReturnTo])

  const openTaskList = useCallback(() => {
    navigate('/task/list')
  }, [navigate])

  const navigateToDetailReturn = useCallback(() => {
    navigate(detailReturnTo)
  }, [detailReturnTo, navigate])

  const onCompositionSubmitted = useCallback((taskId: number) => {
    const nextParams = new URLSearchParams(searchParams)
    nextParams.set('taskId', String(taskId))
    nextParams.set('returnTo', taskReturnTo)
    setSearchParams(nextParams, { replace: true })
  }, [searchParams, setSearchParams, taskReturnTo])

  return {
    creativeId,
    prioritizedTaskId,
    detailDiagnosticsOpen,
    aiClipRequested,
    openAiClipWorkflow,
    closeAiClipWorkflow,
    handleOpenDiagnostics,
    handleCloseDiagnostics,
    openTaskDiagnostics,
    openTaskList,
    navigateToDetailReturn,
    onCompositionSubmitted,
  }
}
