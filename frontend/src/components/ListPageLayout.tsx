import { Row, Col, Card } from 'antd'

interface ListPageLayoutProps {
  title?: string
  filterBar?: React.ReactNode
  actionBar?: React.ReactNode
  children: React.ReactNode
}

export default function ListPageLayout({ filterBar, actionBar, children }: ListPageLayoutProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {(filterBar ?? actionBar) && (
        <Card size="small" styles={{ body: { paddingBlock: 12 } }}>
          <Row justify="space-between" align="middle">
            <Col>{filterBar}</Col>
            <Col>{actionBar}</Col>
          </Row>
        </Card>
      )}
      <Card size="small" styles={{ body: { padding: 0 } }}>
        {children}
      </Card>
    </div>
  )
}
