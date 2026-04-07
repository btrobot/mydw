import { Row, Col } from 'antd'

interface ListPageLayoutProps {
  title?: string
  filterBar?: React.ReactNode
  actionBar?: React.ReactNode
  children: React.ReactNode
}

export default function ListPageLayout({ filterBar, actionBar, children }: ListPageLayoutProps) {
  return (
    <div>
      {(filterBar ?? actionBar) && (
        <Row justify="space-between" align="middle" style={{ marginBottom: 12 }}>
          <Col>{filterBar}</Col>
          <Col>{actionBar}</Col>
        </Row>
      )}
      {children}
    </div>
  )
}
