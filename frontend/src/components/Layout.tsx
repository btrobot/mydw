import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Typography, theme } from 'antd'
import {
  DashboardOutlined,
  UserOutlined,
  FileTextOutlined,
  FolderOutlined,
  ScissorOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const { Header, Sider, Content } = Layout
const { Title } = Typography

const items = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '数据看板' },
  { key: '/account', icon: <UserOutlined />, label: '账号管理' },
  {
    key: 'task-group',
    icon: <FileTextOutlined />,
    label: '任务管理',
    children: [
      { key: '/task/list', label: '任务列表' },
      { key: '/task/assemble', label: '组装任务' },
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
      { type: 'divider' },
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
    ],
  },
]

const subMenuKeys = [
  '/material/overview',
  '/material/video',
  '/material/copywriting',
  '/material/cover',
  '/material/audio',
  '/material/topic',
  '/material/product',
  '/material/topic-group',
  '/task/list',
  '/task/assemble',
  '/schedule-config',
  '/profile-management',
]

export default function LayoutComponent() {
  const navigate = useNavigate()
  const location = useLocation()
  const {
    token: { colorBgContainer },
  } = theme.useToken()

  const isMaterialRoute = location.pathname.startsWith('/material')
  const isSettingsRoute = location.pathname === '/settings'
  const isTaskRoute = location.pathname.startsWith('/task') || ['/schedule-config', '/profile-management'].includes(location.pathname)
  const initialOpenKeys = [
    ...(isMaterialRoute ? ['material-group'] : []),
    ...(isSettingsRoute ? ['settings-group'] : []),
    ...(isTaskRoute ? ['task-group'] : []),
  ]
  const [openKeys, setOpenKeys] = useState<string[]>(initialOpenKeys)

  const selectedKey = subMenuKeys.find((k) => location.pathname === k)
    ?? location.pathname

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', padding: '0 24px' }}>
        <Title level={4} style={{ color: 'white', margin: 0, flexShrink: 0 }}>
          得物掘金工具
        </Title>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: colorBgContainer }}>
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            openKeys={openKeys}
            onOpenChange={setOpenKeys}
            items={items}
            onClick={({ key }) => {
              if (key !== 'material-group' && key !== 'settings-group' && key !== 'task-group') navigate(key)
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
