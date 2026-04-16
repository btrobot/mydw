import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, App as AntApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'

import 'dayjs/locale/zh-cn'

import { AuthBootstrapProvider, AuthErrorBoundary, AuthStatusPage, LoginPage, ProtectedAppShell, PublicLoginRoute, SessionAdmin } from '@/features/auth'
import { QueryProvider } from '@/providers/QueryProvider'
import Dashboard from './pages/Dashboard'
import Account from './pages/Account'
import TaskList from './pages/TaskList'
import AIClip from './pages/AIClip'
import Settings from './pages/Settings'
import ScheduleConfig from './pages/ScheduleConfig'
import ProfileManagement from './pages/ProfileManagement'
import MaterialOverview from './pages/material/MaterialOverview'
import VideoList from './pages/material/VideoList'
import CopywritingList from './pages/material/CopywritingList'
import CoverList from './pages/material/CoverList'
import AudioList from './pages/material/AudioList'
import TopicList from './pages/material/TopicList'
import TopicGroupList from './pages/material/TopicGroupList'
import TopicGroupDetail from './pages/material/TopicGroupDetail'
import ProductList from './pages/product/ProductList'
import ProductDetail from './pages/product/ProductDetail'
import VideoDetail from './pages/material/VideoDetail'
import TaskDetail from './pages/task/TaskDetail'
import CreativeWorkbench from './features/creative/pages/CreativeWorkbench'
import CreativeDetail from './features/creative/pages/CreativeDetail'

import TaskCreate from './pages/task/TaskCreate'

dayjs.locale('zh-cn')

const theme = {
  token: {
    colorPrimary: '#1677ff',
    borderRadius: 6,
    colorBgLayout: '#f0f2f5',
  },
  components: {
    Table: {
      headerBg: '#fafafa',
    },
  },
}

function App() {
  return (
    <ConfigProvider theme={theme} locale={zhCN}>
      <AntApp>
        <QueryProvider>
          <AuthBootstrapProvider>
            <AuthErrorBoundary>
              <HashRouter>
                <Routes>
                  <Route element={<PublicLoginRoute />}>
                    <Route path="login" element={<LoginPage />} />
                  </Route>

                  <Route path="auth/revoked" element={<AuthStatusPage variant="revoked" />} />
                  <Route path="auth/device-mismatch" element={<AuthStatusPage variant="device_mismatch" />} />
                  <Route path="auth/expired" element={<AuthStatusPage variant="expired" />} />
                  <Route path="auth/grace" element={<AuthStatusPage variant="grace" />} />

                  <Route path="/" element={<ProtectedAppShell />}>
                    <Route index element={<Navigate to="/dashboard" replace />} />
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="account" element={<Account />} />
                    <Route path="creative" element={<Navigate to="/creative/workbench" replace />} />
                    <Route path="creative/workbench" element={<CreativeWorkbench />} />
                    <Route path="creative/:id" element={<CreativeDetail />} />
                    <Route path="task" element={<Navigate to="/task/list" replace />} />
                    <Route path="task/list" element={<TaskList />} />
                    <Route path="task/create" element={<TaskCreate />} />

                    <Route path="task/:id" element={<TaskDetail />} />

                    {/* ???? */}
                    <Route path="material" element={<MaterialOverview />} />
                    <Route path="material/overview" element={<MaterialOverview />} />
                    <Route path="material/video" element={<VideoList />} />
                    <Route path="material/video/:id" element={<VideoDetail />} />
                    <Route path="material/copywriting" element={<CopywritingList />} />
                    <Route path="material/cover" element={<CoverList />} />
                    <Route path="material/audio" element={<AudioList />} />
                    <Route path="material/topic-group" element={<TopicGroupList />} />
                    <Route path="material/topic-group/:id" element={<TopicGroupDetail />} />
                    <Route path="material/topic" element={<TopicList />} />

                    {/* ???? */}
                    <Route path="material/product" element={<ProductList />} />
                    <Route path="material/product/:id" element={<ProductDetail />} />

                    <Route path="ai-clip" element={<AIClip />} />
                    <Route path="settings" element={<Settings />} />
                    <Route path="settings/auth-admin" element={<SessionAdmin />} />
                    <Route path="schedule-config" element={<ScheduleConfig />} />
                    <Route path="profile-management" element={<ProfileManagement />} />
                  </Route>
                </Routes>
              </HashRouter>
            </AuthErrorBoundary>
          </AuthBootstrapProvider>
        </QueryProvider>
      </AntApp>
    </ConfigProvider>
  )
}

export default App
