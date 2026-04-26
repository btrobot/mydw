import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons'
import { ProLayout } from '@ant-design/pro-components'
import { Button, Grid, Layout as AntLayout, Typography } from 'antd'
import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

import { AuthSessionHeader } from '@/features/auth'

import {
  getInitialOpenKeys,
  getMenuItemKey,
  getSelectedKey,
  menuTestIds,
  rootMenuPaths,
  shellRoute,
} from './navigation'

const { Title } = Typography
const { Header } = AntLayout
const { useBreakpoint } = Grid

function ShellMenuLabel({ itemKey, children }: { itemKey: string; children: ReactNode }) {
  return <span data-testid={menuTestIds[itemKey]}>{children}</span>
}

function isNarrowViewport() {
  return typeof window !== 'undefined' && window.matchMedia('(max-width: 991.98px)').matches
}

export default function AppShell() {
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
