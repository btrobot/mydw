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
import AIClip from './pages/AIClip'
import Settings from './pages/Settings'
import MaterialOverview from './pages/material/MaterialOverview'
import VideoList from './pages/material/VideoList'
import CopywritingList from './pages/material/CopywritingList'
import CoverList from './pages/material/CoverList'
import AudioList from './pages/material/AudioList'
import TopicList from './pages/material/TopicList'
import ProductList from './pages/product/ProductList'
import ProductDetail from './pages/product/ProductDetail'

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

              {/* 素材中心 */}
              <Route path="material" element={<Navigate to="/material/overview" replace />} />
              <Route path="material/overview" element={<MaterialOverview />} />
              <Route path="material/video" element={<VideoList />} />
              <Route path="material/copywriting" element={<CopywritingList />} />
              <Route path="material/cover" element={<CoverList />} />
              <Route path="material/audio" element={<AudioList />} />
              <Route path="material/topic" element={<TopicList />} />

              {/* 商品管理 */}
              <Route path="product" element={<ProductList />} />
              <Route path="product/:id" element={<ProductDetail />} />

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
