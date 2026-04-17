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
  { key: '/dashboard', icon: <DashboardOutlined />, label: 'Runtime dashboard' },
  { key: '/account', icon: <UserOutlined />, label: 'Accounts' },
  {
    key: 'creative-group',
    icon: <AppstoreOutlined />,
    label: 'Creative workspace',
    children: [
      { key: '/creative/workbench', label: 'Creative workbench' },
    ],
  },
  {
    key: 'task-group',
    icon: <FileTextOutlined />,
    label: 'Execution / diagnostics',
    children: [
      { key: '/task/list', label: 'Task diagnostics list' },
      { key: '/task/create', label: 'Create execution task' },
      { key: '/schedule-config', label: 'Execution scheduling' },
      { key: '/profile-management', label: 'Execution profiles' },
    ],
  },
  {
    key: 'material-group',
    icon: <FolderOutlined />,
    label: 'Materials',
    children: [
      { key: '/material/overview', label: 'Overview' },
      { key: '/material/video', label: 'Videos' },
      { key: '/material/copywriting', label: 'Copywriting' },
      { key: '/material/cover', label: 'Covers' },
      { key: '/material/audio', label: 'Audio' },
      { key: '/material/topic', label: 'Topics' },
      { type: 'divider' as const },
      { key: '/material/product', label: 'Products' },
      { key: '/material/topic-group', label: 'Topic groups' },
    ],
  },
  { key: '/ai-clip', icon: <ScissorOutlined />, label: 'AIClip tool page' },
  {
    key: 'settings-group',
    icon: <SettingOutlined />,
    label: 'Settings',
    children: [
      { key: '/settings', label: 'General settings' },
      { key: '/settings/auth-admin', label: 'Auth sessions' },
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
          Dewu Creator Console
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
