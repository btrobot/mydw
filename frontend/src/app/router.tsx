import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'

import { BusinessEntryRedirect } from '@/app/routes/BusinessEntryRedirect'
import { AuthStatusPage, LoginPage, ProtectedAppShell, PublicLoginRoute, SessionAdmin } from '@/features/auth'
import CreativeDetail from '@/features/creative/pages/CreativeDetail'
import CreativeWorkbench from '@/features/creative/pages/CreativeWorkbench'
import Account from '@/pages/Account'
import AIClip from '@/pages/AIClip'
import Dashboard from '@/pages/Dashboard'
import AudioList from '@/pages/material/AudioList'
import CopywritingList from '@/pages/material/CopywritingList'
import CoverList from '@/pages/material/CoverList'
import MaterialOverview from '@/pages/material/MaterialOverview'
import TopicGroupDetail from '@/pages/material/TopicGroupDetail'
import TopicGroupList from '@/pages/material/TopicGroupList'
import TopicList from '@/pages/material/TopicList'
import VideoDetail from '@/pages/material/VideoDetail'
import VideoList from '@/pages/material/VideoList'
import ProductDetail from '@/pages/product/ProductDetail'
import ProductList from '@/pages/product/ProductList'
import ProfileManagement from '@/pages/ProfileManagement'
import ScheduleConfig from '@/pages/ScheduleConfig'
import Settings from '@/pages/Settings'
import TaskCreate from '@/pages/task/TaskCreate'
import TaskDetail from '@/pages/task/TaskDetail'
import TaskList from '@/pages/TaskList'

export function AppRouter() {
  return (
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
          <Route index element={<BusinessEntryRedirect />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="account" element={<Account />} />
          <Route path="creative" element={<BusinessEntryRedirect />} />
          <Route path="creative/workbench" element={<CreativeWorkbench />} />
          <Route path="creative/:id" element={<CreativeDetail />} />
          <Route path="task" element={<Navigate to="/task/list" replace />} />
          <Route path="task/list" element={<TaskList />} />
          <Route path="task/create" element={<TaskCreate />} />
          <Route path="task/:id" element={<TaskDetail />} />
          <Route path="material" element={<MaterialOverview />} />
          <Route path="material/overview" element={<Navigate to="/material" replace />} />
          <Route path="material/video" element={<VideoList />} />
          <Route path="material/video/:id" element={<VideoDetail />} />
          <Route path="material/copywriting" element={<CopywritingList />} />
          <Route path="material/cover" element={<CoverList />} />
          <Route path="material/audio" element={<AudioList />} />
          <Route path="material/topic-group" element={<TopicGroupList />} />
          <Route path="material/topic-group/:id" element={<TopicGroupDetail />} />
          <Route path="material/topic" element={<TopicList />} />
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
  )
}
