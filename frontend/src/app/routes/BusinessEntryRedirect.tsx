import { Navigate } from 'react-router-dom'

import { PageLoading } from '@/components/feedback/PageLoading'
import { getCreativeFlowDefaultPath } from '@/features/creative/creativeFlow'
import { useSystemConfig } from '@/hooks/useSystem'

export function BusinessEntryRedirect() {
  const { data, isLoading } = useSystemConfig()

  if (isLoading) {
    return (
      <PageLoading
        title="正在加载工作区"
        description="请稍候，系统正在确定默认业务入口。"
        fullHeight
      />
    )
  }

  return <Navigate to={getCreativeFlowDefaultPath(data)} replace />
}
