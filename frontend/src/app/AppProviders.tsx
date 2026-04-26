import { App as AntApp, ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import { type ReactNode } from 'react'

import 'dayjs/locale/zh-cn'

import { AuthBootstrapProvider, AuthErrorBoundary } from '@/features/auth'

import { QueryProvider } from './providers/QueryProvider'
import { appTheme } from './theme'

dayjs.locale('zh-cn')

interface AppProvidersProps {
  children: ReactNode
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <ConfigProvider theme={appTheme} locale={zhCN}>
      <AntApp>
        <QueryProvider>
          <AuthBootstrapProvider>
            <AuthErrorBoundary>
              {children}
            </AuthErrorBoundary>
          </AuthBootstrapProvider>
        </QueryProvider>
      </AntApp>
    </ConfigProvider>
  )
}
