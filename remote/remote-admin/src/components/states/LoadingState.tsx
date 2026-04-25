import { Flex, Spin, Typography } from 'antd';

export function LoadingState({ title }: { title: string }): JSX.Element {
  return (
    <Flex vertical align="center" justify="center" gap={16} style={{ minHeight: 240 }}>
      <Spin size="large" />
      <Typography.Text type="secondary">{title}</Typography.Text>
    </Flex>
  );
}
