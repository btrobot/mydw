import { Button, Layout, Menu, Space, Tag, Typography } from 'antd';
import type { MenuProps } from 'antd';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../features/auth/auth-context.js';

const NAV_ITEMS: MenuProps['items'] = [
  { key: '/dashboard', label: 'Dashboard' },
  { key: '/users', label: 'Users' },
  { key: '/devices', label: 'Devices' },
  { key: '/sessions', label: 'Sessions' },
  { key: '/audit-logs', label: 'Audit Logs' },
];

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/users': 'Users',
  '/devices': 'Devices',
  '/sessions': 'Sessions',
  '/audit-logs': 'Audit Logs',
};

function getRoleTagColor(role: string): string {
  if (role === 'super_admin') return 'red';
  if (role === 'auth_admin') return 'blue';
  return 'default';
}

export function AppShell(): JSX.Element {
  const location = useLocation();
  const navigate = useNavigate();
  const { session, logout } = useAuth();
  const selectedKey = PAGE_TITLES[location.pathname] ? location.pathname : '/dashboard';
  const pageTitle = PAGE_TITLES[selectedKey] ?? 'Remote Admin';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Sider width={232} breakpoint="lg" collapsedWidth={80}>
        <div style={{ padding: 20, color: '#fff' }}>
          <Typography.Title level={4} style={{ color: '#fff', margin: 0 }}>
            Remote Admin Next
          </Typography.Title>
          <Typography.Paragraph style={{ color: 'rgba(255,255,255,0.7)', margin: '8px 0 0' }}>
            Day 3 React shell
          </Typography.Paragraph>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={NAV_ITEMS}
          onClick={({ key }) => navigate(key)}
        />
      </Layout.Sider>

      <Layout>
        <Layout.Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
          }}
        >
          <div>
            <Typography.Title level={4} style={{ margin: 0 }}>
              {pageTitle}
            </Typography.Title>
            <Typography.Text type="secondary">Protected admin control plane</Typography.Text>
          </div>

          <Space size="middle" wrap>
            <div style={{ textAlign: 'right' }}>
              <Typography.Text strong>{session?.user.display_name ?? session?.user.username ?? 'Admin'}</Typography.Text>
              <div>
                <Tag color={getRoleTagColor(session?.user.role ?? '')}>{session?.user.role ?? 'unknown'}</Tag>
              </div>
            </div>
            <Button
              onClick={() => {
                logout();
                navigate('/login', { replace: true });
              }}
            >
              Sign out
            </Button>
          </Space>
        </Layout.Header>

        <Layout.Content style={{ padding: 24 }}>
          <Outlet />
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
