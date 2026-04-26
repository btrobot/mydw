import { Avatar, Button, Layout, Menu, Space, Tag, Typography, theme } from 'antd';
import type { MenuProps } from 'antd';
import { useMemo, useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../features/auth/auth-context.js';

interface NavDefinition {
  key: string;
  label: string;
  description: string;
  shortLabel: string;
}

const NAV_GROUPS: Array<{
  key: string;
  label: string;
  items: NavDefinition[];
}> = [
  {
    key: 'overview',
    label: 'Overview',
    items: [{ key: '/dashboard', label: 'Dashboard', description: 'Live metrics and operator queue', shortLabel: 'DB' }],
  },
  {
    key: 'directory',
    label: 'Directory',
    items: [
      { key: '/users', label: 'Users', description: 'Accounts, licenses, and entitlements', shortLabel: 'US' },
      { key: '/devices', label: 'Devices', description: 'Bindings, versions, and device state', shortLabel: 'DV' },
      { key: '/sessions', label: 'Sessions', description: 'Live auth continuity and revocation', shortLabel: 'SE' },
    ],
  },
  {
    key: 'compliance',
    label: 'Compliance',
    items: [{ key: '/audit-logs', label: 'Audit logs', description: 'Event tracing and destructive actions', shortLabel: 'AU' }],
  },
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

function renderNavIcon(shortLabel: string): JSX.Element {
  return (
    <Avatar
      size={30}
      shape="square"
      style={{
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.92), rgba(37, 99, 235, 0.78))',
        color: '#eff6ff',
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: '0.08em',
      }}
    >
      {shortLabel}
    </Avatar>
  );
}

function renderNavLabel(title: string, description: string): JSX.Element {
  return (
    <div style={{ display: 'grid', gap: 2, minWidth: 0 }}>
      <span
        style={{
          color: 'inherit',
          fontSize: 14,
          fontWeight: 600,
          lineHeight: '20px',
        }}
      >
        {title}
      </span>
      <span
        style={{
          color: 'rgba(226, 232, 240, 0.72)',
          fontSize: 12,
          lineHeight: '16px',
          whiteSpace: 'normal',
        }}
      >
        {description}
      </span>
    </div>
  );
}

export function AppShell(): JSX.Element {
  const location = useLocation();
  const navigate = useNavigate();
  const { session, logout } = useAuth();
  const { token } = theme.useToken();
  const [collapsed, setCollapsed] = useState(false);
  const selectedKey = PAGE_TITLES[location.pathname] ? location.pathname : '/dashboard';
  const pageTitle = PAGE_TITLES[selectedKey] ?? 'Remote Admin';
  const navItems = useMemo<MenuProps['items']>(
    () =>
      NAV_GROUPS.map((group) => ({
        type: 'group',
        key: group.key,
        label: group.label,
        children: group.items.map((item) => ({
          key: item.key,
          icon: renderNavIcon(item.shortLabel),
          label: renderNavLabel(item.label, item.description),
        })),
      })),
    [],
  );

  return (
    <Layout style={{ minHeight: '100vh', background: token.colorBgLayout }}>
      <Layout.Sider
        width={280}
        breakpoint="lg"
        collapsedWidth={88}
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{
          borderInlineEnd: '1px solid rgba(148, 163, 184, 0.14)',
          boxShadow: 'inset -1px 0 0 rgba(255, 255, 255, 0.04)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            display: 'flex',
            minHeight: '100%',
            flexDirection: 'column',
            gap: 18,
            padding: '16px 16px 72px',
            background:
              'radial-gradient(circle at top, rgba(37, 99, 235, 0.22), transparent 34%), linear-gradient(180deg, rgba(8, 21, 35, 1), rgba(10, 25, 41, 1))',
          }}
        >
          <div
            style={{
              borderRadius: token.borderRadiusLG,
              border: '1px solid rgba(148, 163, 184, 0.16)',
              background: 'rgba(15, 23, 42, 0.56)',
              padding: collapsed ? '14px 10px' : '18px 16px',
              color: '#f8fafc',
            }}
          >
            <Space direction="vertical" size={collapsed ? 10 : 6} style={{ width: '100%' }}>
              <Avatar
                size={collapsed ? 36 : 42}
                shape="square"
                style={{
                  background: 'linear-gradient(135deg, #38bdf8, #2563eb)',
                  color: '#eff6ff',
                  fontWeight: 700,
                  fontSize: collapsed ? 14 : 16,
                  alignSelf: collapsed ? 'center' : 'flex-start',
                }}
              >
                RA
              </Avatar>
              {!collapsed ? (
                <>
                  <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#7dd3fc' }}>
                    Remote control plane
                  </div>
                  <Typography.Title level={4} style={{ color: '#f8fafc', margin: 0 }}>
                    Remote Admin
                  </Typography.Title>
                  <Typography.Paragraph style={{ color: 'rgba(226,232,240,0.72)', margin: 0 }}>
                    Protected operator shell for identity, devices, sessions, and audit review.
                  </Typography.Paragraph>
                </>
              ) : null}
            </Space>
          </div>

          <div style={{ flex: 1, minHeight: 0 }}>
            <Menu
              theme="dark"
              mode="inline"
              inlineCollapsed={collapsed}
              selectedKeys={[selectedKey]}
              items={navItems}
              onClick={({ key }) => navigate(key)}
              style={{ background: 'transparent', border: 'none' }}
            />
          </div>

          <div
            style={{
              borderRadius: token.borderRadiusLG,
              border: '1px solid rgba(148, 163, 184, 0.16)',
              background: 'rgba(15, 23, 42, 0.5)',
              padding: collapsed ? 10 : 14,
            }}
          >
            {collapsed ? (
              <Avatar
                size={34}
                style={{
                  background: 'rgba(59, 130, 246, 0.22)',
                  color: '#bfdbfe',
                  display: 'flex',
                  marginInline: 'auto',
                }}
              >
                {session?.user.display_name?.slice(0, 1) ?? session?.user.username?.slice(0, 1) ?? 'A'}
              </Avatar>
            ) : (
              <Space direction="vertical" size={8} style={{ width: '100%' }}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#94a3b8' }}>
                  Operator access
                </div>
                <div style={{ color: '#f8fafc', fontWeight: 600 }}>
                  {session?.user.display_name ?? session?.user.username ?? 'Admin'}
                </div>
                <Space size={[8, 8]} wrap>
                  <Tag color={getRoleTagColor(session?.user.role ?? '')}>{session?.user.role ?? 'unknown'}</Tag>
                  <Tag bordered={false} color="processing">
                    Session protected
                  </Tag>
                </Space>
                <Typography.Text style={{ color: 'rgba(226,232,240,0.72)' }}>
                  Destructive actions require step-up verification before the API call is allowed.
                </Typography.Text>
              </Space>
            )}
          </div>
        </div>
      </Layout.Sider>

      <Layout>
        <Layout.Header
          style={{
            background: token.colorBgContainer,
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
            borderBottom: '1px solid rgba(148, 163, 184, 0.16)',
          }}
        >
          <div>
            <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>
              Remote admin workspace
            </Typography.Text>
            <Typography.Title level={4} style={{ margin: 0 }}>
              {pageTitle}
            </Typography.Title>
            <Typography.Text type="secondary">Protected admin control plane with role-aware destructive safeguards.</Typography.Text>
          </div>

          <Space size="middle" wrap>
            <div
              style={{
                textAlign: 'right',
                padding: '8px 12px',
                borderRadius: token.borderRadius,
                background: 'rgba(248, 250, 252, 0.96)',
                border: '1px solid rgba(148, 163, 184, 0.16)',
              }}
            >
              <Typography.Text strong>{session?.user.display_name ?? session?.user.username ?? 'Admin'}</Typography.Text>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
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

        <Layout.Content style={{ padding: 28, background: token.colorBgLayout }}>
          <Outlet />
        </Layout.Content>
      </Layout>
    </Layout>
  );
}
