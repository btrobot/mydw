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
import { useMemo, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

import { AuthSessionHeader } from '@/features/auth'

const { Header, Sider, Content } = Layout
const { Title } = Typography
const { useBreakpoint } = Grid

const subMenuKeys = [
  '/creative/workbench',
  '/material/video',
  '/material/copywriting',
  '/material/cover',
  '/material/audio',
  '/material/topic',
  '/material/product',
  '/material/topic-group',
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

  const items = useMemo(() => ([
    {
      key: 'creative-group',
      icon: <AppstoreOutlined />,
      label: '创作工作台',
      children: [
        { key: '/creative/workbench', label: '作品工作台' },
      ],
    },
    { key: '/dashboard', icon: <DashboardOutlined />, label: '运行总览' },
    { key: '/account', icon: <UserOutlined />, label: '账号' },
    {
      key: 'task-group',
      icon: <FileTextOutlined />,
      label: (
        <span
          onClick={() => {
            navigate('/task/list')
          }}
        >
          任务管理
        </span>
      ),
      children: [
        { key: '/schedule-config', label: '执行调度' },
        { key: '/profile-management', label: '合成配置' },
      ],
    },
    {
      key: 'material-group',
      icon: <FolderOutlined />,
      label: (
        <span
          onClick={() => {
            navigate('/material')
          }}
        >
          素材管理
        </span>
      ),
      children: [
        { key: '/material/video', label: '视频' },
        { key: '/material/copywriting', label: '文案' },
        { key: '/material/cover', label: '封面' },
        { key: '/material/audio', label: '音频' },
        { key: '/material/topic', label: '话题' },
        { type: 'divider' as const },
        { key: '/material/product', label: '商品' },
        { key: '/material/topic-group', label: '话题组' },
      ],
    },
    { key: '/ai-clip', icon: <ScissorOutlined />, label: 'AIClip 工作流' },
    {
      key: 'settings-group',
      icon: <SettingOutlined />,
      label: '设置',
      children: [
        { key: '/settings', label: '通用设置' },
        { key: '/settings/auth-admin', label: '授权会话' },
      ],
    },
  ]), [navigate])

  const selectedKey = subMenuKeys.find((key) => location.pathname === key)
    ?? (location.pathname === '/material' ? 'material-group' : undefined)
    ?? (location.pathname === '/task/list' || location.pathname === '/task/create' ? 'task-group' : undefined)
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
          得物创作控制台
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
