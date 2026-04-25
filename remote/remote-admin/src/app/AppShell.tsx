import { Button, Layout, Space, Typography } from 'antd';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../features/auth/auth-context.js';

const { Header, Content } = Layout;

export function AppShell(): JSX.Element {
  const navigate = useNavigate();
  const location = useLocation();
  const { session, logout } = useAuth();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#111827',
          paddingInline: 24,
        }}
      >
        <Space direction="vertical" size={0}>
          <Typography.Text style={{ color: '#fff', fontSize: 16 }}>
            Remote Admin Next
          </Typography.Text>
          <Typography.Text style={{ color: 'rgba(255,255,255,0.65)' }}>
            {location.pathname || '/dashboard'}
          </Typography.Text>
        </Space>
        <Space size="middle">
          <Typography.Text style={{ color: '#fff' }}>
            {session?.user.display_name ?? session?.user.username ?? 'Admin'}
          </Typography.Text>
          <Button
            onClick={() => {
              logout();
              navigate('/login', { replace: true });
            }}
          >
            退出登录
          </Button>
        </Space>
      </Header>
      <Content style={{ padding: 24 }}>
        <Outlet />
      </Content>
    </Layout>
  );
}
