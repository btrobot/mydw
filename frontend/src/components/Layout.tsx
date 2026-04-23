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
import { ProLayout } from '@ant-design/pro-components'
import type { MenuDataItem } from '@ant-design/pro-components'
import { Button, Grid, Layout as AntLayout, Typography } from 'antd'
import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

import { AuthSessionHeader } from '@/features/auth'

const { Title } = Typography
const { Header } = AntLayout
const { useBreakpoint } = Grid

type ShellMenuItem = MenuDataItem & {
  key: string
  path?: string
  children?: ShellMenuItem[]
}

const subMenuKeys = [
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

const rootMenuPaths: Record<string, string> = {
  'task-group': '/task/list',
  'material-group': '/material',
}

const menuTestIds: Record<string, string> = {
  '/creative/workbench': 'app-shell-menu-creative-workbench',
  '/dashboard': 'app-shell-menu-dashboard',
  '/account': 'app-shell-menu-account',
  'task-group': 'app-shell-menu-task-group',
  '/schedule-config': 'app-shell-menu-schedule-config',
  '/profile-management': 'app-shell-menu-profile-management',
  'material-group': 'app-shell-menu-material-group',
  '/material/video': 'app-shell-menu-material-video',
  '/material/copywriting': 'app-shell-menu-material-copywriting',
  '/material/cover': 'app-shell-menu-material-cover',
  '/material/audio': 'app-shell-menu-material-audio',
  '/material/topic': 'app-shell-menu-material-topic',
  '/material/product': 'app-shell-menu-material-product',
  '/material/topic-group': 'app-shell-menu-material-topic-group',
  '/ai-clip': 'app-shell-menu-ai-clip',
  'settings-group': 'app-shell-menu-settings-group',
  '/settings': 'app-shell-menu-settings',
  '/settings/auth-admin': 'app-shell-menu-auth-admin',
}

const shellMenuItems: ShellMenuItem[] = [
  { key: '/creative/workbench', path: '/creative/workbench', icon: <AppstoreOutlined />, name: '作品工作台' },
  { key: '/dashboard', path: '/dashboard', icon: <DashboardOutlined />, name: '运行总览' },
  { key: '/account', path: '/account', icon: <UserOutlined />, name: '账号' },
  {
    key: 'task-group',
    path: rootMenuPaths['task-group'],
    icon: <FileTextOutlined />,
    name: '任务管理',
    children: [
      { key: '/schedule-config', path: '/schedule-config', name: '执行调度' },
      { key: '/profile-management', path: '/profile-management', name: '合成配置' },
    ],
  },
  {
    key: 'material-group',
    path: rootMenuPaths['material-group'],
    icon: <FolderOutlined />,
    name: '素材管理',
    children: [
      { key: '/material/video', path: '/material/video', name: '视频' },
      { key: '/material/copywriting', path: '/material/copywriting', name: '文案' },
      { key: '/material/cover', path: '/material/cover', name: '封面' },
      { key: '/material/audio', path: '/material/audio', name: '音频' },
      { key: '/material/topic', path: '/material/topic', name: '话题' },
      { key: '/material/product', path: '/material/product', name: '商品' },
      { key: '/material/topic-group', path: '/material/topic-group', name: '话题组' },
    ],
  },
  { key: '/ai-clip', path: '/ai-clip', icon: <ScissorOutlined />, name: 'AIClip 工作流' },
  {
    key: 'settings-group',
    icon: <SettingOutlined />,
    name: '设置',
    children: [
      { key: '/settings', path: '/settings', name: '通用设置' },
      { key: '/settings/auth-admin', path: '/settings/auth-admin', name: '授权会话' },
    ],
  },
]

const shellRoute = {
  path: '/',
  routes: shellMenuItems,
}

function ShellMenuLabel({ itemKey, children }: { itemKey: string; children: ReactNode }) {
  return <span data-testid={menuTestIds[itemKey]}>{children}</span>
}

function getMenuItemKey(item: MenuDataItem) {
  return String(item.key ?? item.path ?? '')
}

function getInitialOpenKeys(pathname: string) {
  const isMaterialRoute = pathname.startsWith('/material')
  const isSettingsRoute = pathname.startsWith('/settings')
  const isTaskRoute = pathname.startsWith('/task') || ['/schedule-config', '/profile-management'].includes(pathname)

  return [
    ...(isMaterialRoute ? ['material-group'] : []),
    ...(isSettingsRoute ? ['settings-group'] : []),
    ...(isTaskRoute ? ['task-group'] : []),
  ]
}

function getSelectedKey(pathname: string) {
  const isCreativeRoute = pathname.startsWith('/creative')

  return subMenuKeys.find((key) => pathname === key)
    ?? (pathname === '/material' ? 'material-group' : undefined)
    ?? (pathname === '/task/list' || pathname === '/task/create' ? 'task-group' : undefined)
    ?? (isCreativeRoute ? '/creative/workbench' : undefined)
    ?? pathname
}

function isNarrowViewport() {
  return typeof window !== 'undefined' && window.matchMedia('(max-width: 991.98px)').matches
}

export default function LayoutComponent() {
  const navigate = useNavigate()
  const location = useLocation()
  const screens = useBreakpoint()
  const [openKeys, setOpenKeys] = useState<string[]>(() => getInitialOpenKeys(location.pathname))
  const [collapsed, setCollapsed] = useState(() => isNarrowViewport())
  const [isMobileShell, setIsMobileShell] = useState(() => isNarrowViewport())

  useEffect(() => {
    const query = window.matchMedia('(max-width: 991.98px)')
    const syncShellBreakpoint = () => {
      setIsMobileShell(query.matches)
      setCollapsed(query.matches)
    }

    syncShellBreakpoint()
    query.addEventListener('change', syncShellBreakpoint)
    return () => query.removeEventListener('change', syncShellBreakpoint)
  }, [])

  const selectedKey = getSelectedKey(location.pathname)

  const navigateToMenuPath = (path?: string) => {
    if (!path) return
    navigate(path)
    if (isMobileShell) {
      setCollapsed(true)
    }
  }

  return (
    <AntLayout style={{ minHeight: '100vh' }} data-testid="app-shell">
      <Header
        data-testid="app-shell-header"
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
      <ProLayout
        route={shellRoute}
        location={{ pathname: selectedKey }}
        layout="side"
        navTheme="light"
        title={false}
        logo={false}
        menuHeaderRender={false}
        // ProLayout does not render a desktop header for `layout="side"`,
        // so the shell header above remains the canonical app header.
        headerRender={false}
        breakpoint="lg"
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        openKeys={openKeys}
        onOpenChange={(keys) => setOpenKeys(keys || [])}
        menu={{ locale: false, hideMenuWhenCollapsed: true }}
        menuProps={{
          selectedKeys: [selectedKey],
        }}
        contentStyle={{
          padding: screens.md ? 24 : 16,
          minHeight: 360,
        }}
        rightContentRender={false}
        collapsedButtonRender={false}
        menuContentRender={(props, defaultDom) => (
          <div
            data-testid="app-shell-sider"
            className={collapsed || props.collapsed ? 'ant-layout-sider-collapsed' : undefined}
          >
            <div data-testid="app-shell-menu">{defaultDom}</div>
          </div>
        )}
        menuTextRender={(item, defaultDom) => (
          <ShellMenuLabel itemKey={getMenuItemKey(item)}>{defaultDom}</ShellMenuLabel>
        )}
        menuItemRender={(item, defaultDom) => (
          <span
            onClick={(event) => {
              event.preventDefault()
              navigateToMenuPath(item.path)
            }}
          >
            {defaultDom}
          </span>
        )}
        subMenuItemRender={(item, defaultDom) => (
          <span
            onClick={() => {
              navigateToMenuPath(rootMenuPaths[getMenuItemKey(item)])
            }}
          >
            {defaultDom}
          </span>
        )}
      >
        <div data-testid="app-shell-content" style={{ minHeight: 360 }}>
          <Outlet />
        </div>
      </ProLayout>
    </AntLayout>
  )
}
