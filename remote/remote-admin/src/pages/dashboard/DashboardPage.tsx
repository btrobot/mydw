import { Alert, Card, Col, Row, Space, Statistic, Typography } from 'antd';
import { useQuery } from '@tanstack/react-query';

import { ErrorState } from '../../components/states/ErrorState.js';
import { LoadingState } from '../../components/states/LoadingState.js';
import { getDashboardMetrics } from '../../features/auth/auth-client.js';
import { useAuth } from '../../features/auth/auth-context.js';

export function DashboardPage(): JSX.Element {
  const { accessToken, session } = useAuth();

  const metricsQuery = useQuery({
    queryKey: ['dashboardMetrics'],
    queryFn: () => getDashboardMetrics(accessToken ?? ''),
    enabled: Boolean(accessToken),
  });

  if (!accessToken) {
    return <ErrorState title="Admin session missing" description="Please sign in again before loading dashboard metrics." />;
  }

  if (metricsQuery.isLoading) {
    return <LoadingState title="Loading dashboard metrics" />;
  }

  if (metricsQuery.isError || !metricsQuery.data) {
    return (
      <ErrorState
        title="Dashboard metrics unavailable"
        description="The new React shell is up, but the dashboard metric request failed."
        retryLabel="Retry metrics"
        onRetry={() => void metricsQuery.refetch()}
      />
    );
  }

  const metrics = metricsQuery.data;

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Title level={2} style={{ marginBottom: 8 }}>
          Dashboard
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          Signed in as {session?.user.display_name ?? session?.user.username}. This is the Day 2 React shell backed by the existing admin API.
        </Typography.Paragraph>
      </div>

      <Alert
        type="info"
        showIcon
        message="Migration status"
        description="Dashboard is the first fully mounted protected page in the new React shell. Users / devices / sessions / audit stay on the migration queue."
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} xl={6}>
          <Card>
            <Statistic title="Active sessions" value={metrics.active_sessions} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card>
            <Statistic title="Login failures" value={metrics.login_failures} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card>
            <Statistic title="Device mismatches" value={metrics.device_mismatches} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card>
            <Statistic title="Destructive actions" value={metrics.destructive_actions} />
          </Card>
        </Col>
      </Row>

      <Typography.Text type="secondary">Generated at: {metrics.generated_at}</Typography.Text>
    </Space>
  );
}
