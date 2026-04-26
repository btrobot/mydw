import {
  AppstoreOutlined,
  DashboardOutlined,
  FileTextOutlined,
  FolderOutlined,
  ScissorOutlined,
  SettingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import type { MenuDataItem } from '@ant-design/pro-components'

export type ShellMenuItem = MenuDataItem & {
  key: string
  path?: string
  children?: ShellMenuItem[]
}

export const subMenuKeys = [
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

export const rootMenuPaths: Record<string, string> = {
  'task-group': '/task/list',
  'material-group': '/material',
}

export const menuTestIds: Record<string, string> = {
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

export const shellMenuItems: ShellMenuItem[] = [
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

export const shellRoute = {
  path: '/',
  routes: shellMenuItems,
}

export function getMenuItemKey(item: MenuDataItem) {
  return String(item.key ?? item.path ?? '')
}

export function getInitialOpenKeys(pathname: string) {
  const isMaterialRoute = pathname.startsWith('/material')
  const isSettingsRoute = pathname.startsWith('/settings')
  const isTaskRoute = pathname.startsWith('/task') || ['/schedule-config', '/profile-management'].includes(pathname)

  return [
    ...(isMaterialRoute ? ['material-group'] : []),
    ...(isSettingsRoute ? ['settings-group'] : []),
    ...(isTaskRoute ? ['task-group'] : []),
  ]
}

export function getSelectedKey(pathname: string) {
  const isCreativeRoute = pathname.startsWith('/creative')

  return subMenuKeys.find((key) => pathname === key)
    ?? (pathname === '/material' ? 'material-group' : undefined)
    ?? (pathname === '/task/list' || pathname === '/task/create' ? 'task-group' : undefined)
    ?? (isCreativeRoute ? '/creative/workbench' : undefined)
    ?? pathname
}
