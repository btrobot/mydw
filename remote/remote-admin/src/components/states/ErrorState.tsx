import { Button, Result } from 'antd';

type ErrorStateProps = {
  title: string;
  description: string;
  retryLabel?: string;
  onRetry?: () => void;
};

export function ErrorState({ title, description, retryLabel = 'Retry', onRetry }: ErrorStateProps): JSX.Element {
  return (
    <Result
      status="error"
      title={title}
      subTitle={description}
      extra={
        onRetry ? (
          <Button type="primary" onClick={onRetry}>
            {retryLabel}
          </Button>
        ) : null
      }
    />
  );
}
