import { Tag, Tooltip } from 'antd'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  MinusCircleOutlined,
} from '@ant-design/icons'

type AccountStatus = 'active' | 'inactive' | 'logging_in' | 'error' | 'session_expired' | 'disabled'

interface StatusConfig {
  color: string
  icon: JSX.Element
  text: string
}

interface StatusBadgeProps {
  status: string
  showText?: boolean
}

const STATUS_CONFIG: Record<AccountStatus, StatusConfig> = {
  active: {
    color: 'success',
    icon: <CheckCircleOutlined />,
    text: '已登录',
  },
  inactive: {
    color: 'default',
    icon: <ClockCircleOutlined />,
    text: '未登录',
  },
  logging_in: {
    color: 'processing',
    icon: <LoadingOutlined />,
    text: '登录中',
  },
  error: {
    color: 'error',
    icon: <ExclamationCircleOutlined />,
    text: '异常',
  },
  session_expired: {
    color: 'warning',
    icon: <ExclamationCircleOutlined />,
    text: '会话过期',
  },
  disabled: {
    color: 'default',
    icon: <MinusCircleOutlined />,
    text: '已禁用',
  },
}

const DEFAULT_CONFIG: StatusConfig = {
  color: 'default',
  icon: <ClockCircleOutlined />,
  text: '未知',
}

export default function StatusBadge({ status, showText = true }: StatusBadgeProps) {
  const config = (STATUS_CONFIG as Record<string, StatusConfig>)[status] || DEFAULT_CONFIG
  const isLoggingIn = status === 'logging_in'

  return (
    <Tooltip title={`状态: ${config.text}`}>
      <Tag
        color={config.color}
        icon={isLoggingIn ? <LoadingOutlined spin /> : config.icon}
      >
        {showText && config.text}
      </Tag>
    </Tooltip>
  )
}

// Export type for external use
export type { AccountStatus, StatusConfig }
