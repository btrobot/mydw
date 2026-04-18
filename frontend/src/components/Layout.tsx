import {
  AppstoreOutlined,
  DashboardOutlined,
  FileTextOutlined,
  FolderOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ScissorOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Button, Grid, Layout, Menu, Typography, theme } from 'antd'
import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

import { AuthSessionHeader } from '@/features/auth'

const { Header, Sider, Content } = Layout
const { Title } = Typography
const { useBreakpoint } = Grid

const items = [
  {
    key: 'creative-group',
    icon: <AppstoreOutlined />,
    label: '\u521b\u4f5c\u5de5\u4f5c\u53f0',
    children: [
      { key: '/creative/workbench', label: '\u4f5c\u54c1\u5de5\u4f5c\u53f0' },
    ],
  },
  { key: '/dashboard', icon: <DashboardOutlined />, label: '\u8fd0\u884c\u603b\u89c8' },
  { key: '/account', icon: <UserOutlined />, label: '\u8d26\u53f7' },
  {
    key: 'task-group',
    icon: <FileTextOutlined />,
    label: '\u6267\u884c\u4e0e\u8bca\u65ad',
    children: [
      { key: '/task/list', label: '\u4efb\u52a1\u8bca\u65ad\u5217\u8868' },
      { key: '/task/create', label: '\u65b0\u5efa\u6267\u884c\u4efb\u52a1' },
      { key: '/schedule-config', label: '\u6267\u884c\u8c03\u5ea6' },
      { key: '/profile-management', label: '\u6267\u884c\u914d\u7f6e' },
    ],
  },
  {
    key: 'material-group',
    icon: <FolderOutlined />,
    label: '\u7d20\u6750',
    children: [
      { key: '/material/overview', label: '\u603b\u89c8' },
      { key: '/material/video', label: '\u89c6\u9891' },
      { key: '/material/copywriting', label: '\u6587\u6848' },
      { key: '/material/cover', label: '\u5c01\u9762' },
      { key: '/material/audio', label: '\u97f3\u9891' },
      { key: '/material/topic', label: '\u8bdd\u9898' },
      { type: 'divider' as const },
      { key: '/material/product', label: '\u5546\u54c1' },
      { key: '/material/topic-group', label: '\u8bdd\u9898\u7ec4' },
    ],
  },
  { key: '/ai-clip', icon: <ScissorOutlined />, label: 'AIClip \u5de5\u4f5c\u6d41' },
  {
    key: 'settings-group',
    icon: <SettingOutlined />,
    label: '\u8bbe\u7f6e',
    children: [
      { key: '/settings', label: '\u901a\u7528\u8bbe\u7f6e' },
      { key: '/settings/auth-admin', label: '\u6388\u6743\u4f1a\u8bdd' },
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
  const screens = useBreakpoint()
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
  const [collapsed, setCollapsed] = useState(false)
  const [isBroken, setIsBroken] = useState(false)

  const selectedKey = subMenuKeys.find((key) => location.pathname === key)
    ?? (isCreativeRoute ? '/creative/workbench' : undefined)
    ?? location.pathname

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: screens.md ? '0 24px' : '0 16px',
        }}
      >
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={() => setCollapsed((current) => !current)}
          style={{ color: 'white' }}
          aria-label="toggle-navigation"
        />
        <Title
          level={screens.md ? 4 : 5}
          style={{ color: 'white', margin: 0, flex: 1, minWidth: 0 }}
          ellipsis
        >
          \u5f97\u7269\u521b\u4f5c\u63a7\u5236\u53f0
        </Title>
        <div style={{ marginLeft: 'auto', minWidth: 0 }}>
          <AuthSessionHeader />
        </div>
      </Header>
      <Layout>
        <Sider
          width={220}
          breakpoint="lg"
          collapsedWidth={isBroken ? 0 : 80}
          collapsible
          collapsed={collapsed}
          onCollapse={(value) => setCollapsed(value)}
          onBreakpoint={(broken) => {
            setIsBroken(broken)
            setCollapsed(broken)
          }}
          style={{ background: colorBgContainer }}
        >
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            openKeys={openKeys}
            onOpenChange={(keys) => setOpenKeys(keys as string[])}
            items={items}
            onClick={({ key }) => {
              if (!rootMenuKeys.has(key)) {
                navigate(key)
                if (isBroken) {
                  setCollapsed(true)
                }
              }
            }}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Layout style={{ padding: screens.md ? '24px' : '16px' }}>
          <Content style={{ minHeight: 360 }}>
            <Outlet />
          </Content>
        </Layout>
      </Layout>
    </Layout>
  )
}
