import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'

import 'dayjs/locale/zh-cn'

import { QueryProvider } from '@/providers/QueryProvider'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Account from './pages/Account'
import Task from './pages/Task'
import Material from './pages/Material'
import AIClip from './pages/AIClip'
import Settings from './pages/Settings'

dayjs.locale('zh-cn')

const theme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
  },
}

function App() {
  return (
    <ConfigProvider theme={theme} locale={zhCN}>
      <QueryProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="account" element={<Account />} />
              <Route path="task" element={<Task />} />
              <Route path="material" element={<Material />} />
              <Route path="ai-clip" element={<AIClip />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryProvider>
    </ConfigProvider>
  )
}

export default App
