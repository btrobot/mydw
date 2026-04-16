import {
  AppstoreOutlined,
  DashboardOutlined,
  FileTextOutlined,
  FolderOutlined,
  ScissorOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Layout, Menu, Typography, theme } from 'antd'
import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

import { AuthSessionHeader } from '@/features/auth'

const { Header, Sider, Content } = Layout
const { Title } = Typography

const items = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '数据看板' },
  { key: '/account', icon: <UserOutlined />, label: '账号管理' },
  {
    key: 'creative-group',
    icon: <AppstoreOutlined />,
    label: '作品工作台',
    children: [
      { key: '/creative/workbench', label: '作品列表' },
    ],
  },
  {
    key: 'task-group',
    icon: <FileTextOutlined />,
    label: '任务管理',
    children: [
      { key: '/task/list', label: '任务列表' },
      { key: '/task/create', label: '创建任务' },
      { key: '/schedule-config', label: '调度配置' },
      { key: '/profile-management', label: '配置档管理' },
    ],
  },
  {
    key: 'material-group',
    icon: <FolderOutlined />,
    label: '素材中心',
    children: [
      { key: '/material/overview', label: '素材总览' },
      { key: '/material/video', label: '视频管理' },
      { key: '/material/copywriting', label: '文案管理' },
      { key: '/material/cover', label: '封面管理' },
      { key: '/material/audio', label: '音频管理' },
      { key: '/material/topic', label: '话题管理' },
      { type: 'divider' as const },
      { key: '/material/product', label: '商品管理' },
      { key: '/material/topic-group', label: '话题组管理' },
    ],
  },
  { key: '/ai-clip', icon: <ScissorOutlined />, label: 'AI 剪辑' },
  {
    key: 'settings-group',
    icon: <SettingOutlined />,
    label: '系统设置',
    children: [
      { key: '/settings', label: '基本设置' },
      { key: '/settings/auth-admin', label: '授权会话' },
    ],
  },
]

const subMenuKeys = [
  '/creative/workbench',
  '/material/overview',
  '/material/video',
  '/material/copywriting',
  '/material/cover',
  '/material/audio',
  '/material/topic',
  '/material/product',
  '/material/topic-group',
  '/task/list',
  '/task/create',
  '/schedule-config',
  '/profile-management',
  '/settings/auth-admin',
]

const rootMenuKeys = new Set(['material-group', 'creative-group', 'settings-group', 'task-group'])

export default function LayoutComponent() {
  const navigate = useNavigate()
  const location = useLocation()
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  const isMaterialRoute = location.pathname.startsWith('/material')
  const isCreativeRoute = location.pathname.startsWith('/creative')
  const isSettingsRoute = location.pathname.startsWith('/settings')
  const isTaskRoute =
    location.pathname.startsWith('/task')
    || ['/schedule-config', '/profile-management'].includes(location.pathname)

  const initialOpenKeys = [
    ...(isMaterialRoute ? ['material-group'] : []),
    ...(isCreativeRoute ? ['creative-group'] : []),
    ...(isSettingsRoute ? ['settings-group'] : []),
    ...(isTaskRoute ? ['task-group'] : []),
  ]
  const [openKeys, setOpenKeys] = useState<string[]>(initialOpenKeys)

  const selectedKey = subMenuKeys.find((key) => location.pathname === key)
    ?? (isCreativeRoute ? '/creative/workbench' : undefined)
    ?? location.pathname

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <Title level={4} style={{ color: 'white', margin: 0, flexShrink: 0 }}>
          得物掘金工具
        </Title>
        <div style={{ marginLeft: 'auto' }}>
          <AuthSessionHeader />
        </div>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: colorBgContainer }}>
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            openKeys={openKeys}
            onOpenChange={(keys) => setOpenKeys(keys as string[])}
            items={items}
            onClick={({ key }) => {
              if (!rootMenuKeys.has(key)) {
                navigate(key)
              }
            }}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content style={{ minHeight: 360 }}>
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}
