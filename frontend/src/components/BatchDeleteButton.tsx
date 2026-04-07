import { Button, Popconfirm } from 'antd'
import { DeleteOutlined } from '@ant-design/icons'

interface BatchDeleteButtonProps {
  count: number
  onConfirm: () => void
  loading?: boolean
}

export default function BatchDeleteButton({ count, onConfirm, loading }: BatchDeleteButtonProps) {
  if (count === 0) return null

  return (
    <Popconfirm title={`确定删除 ${count} 项？`} onConfirm={onConfirm}>
      <Button danger icon={<DeleteOutlined />} loading={loading}>
        批量删除 ({count})
      </Button>
    </Popconfirm>
  )
}
