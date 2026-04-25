import { Empty } from 'antd';

export function EmptyState({ description }: { description: string }): JSX.Element {
  return <Empty description={description} image={Empty.PRESENTED_IMAGE_SIMPLE} />;
}
