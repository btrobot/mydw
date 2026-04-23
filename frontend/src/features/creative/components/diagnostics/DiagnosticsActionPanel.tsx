import { Alert, Button, Card, Space, Typography } from 'antd'

const { Text } = Typography

export type DiagnosticsRecommendation = {
  actionLabel?: string
  evidence: string[]
  key: string
  onAction?: () => void
  severity: 'success' | 'info' | 'warning' | 'error'
  testId?: string
  title: string
}

type DiagnosticsActionPanelProps = {
  recommendations: DiagnosticsRecommendation[]
  testId: string
  title: string
}

export default function DiagnosticsActionPanel({
  recommendations,
  testId,
  title,
}: DiagnosticsActionPanelProps) {
  return (
    <Card size="small" title={title} data-testid={testId}>
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        {recommendations.map((recommendation) => (
          <Alert
            key={recommendation.key}
            type={recommendation.severity}
            showIcon
            message={recommendation.title}
            description={(
              <Space direction="vertical" size={6} style={{ width: '100%' }}>
                {recommendation.evidence.map((item, index) => (
                  <Text key={`${recommendation.key}-evidence-${index}`} type="secondary">
                    {item}
                  </Text>
                ))}
              </Space>
            )}
            action={recommendation.onAction && recommendation.actionLabel ? (
              <Button size="small" onClick={recommendation.onAction} data-testid={recommendation.testId}>
                {recommendation.actionLabel}
              </Button>
            ) : undefined}
          />
        ))}
      </Space>
    </Card>
  )
}
