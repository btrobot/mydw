/**
 * LoginModal - 账号登录弹窗组件
 *
 * 提供手机验证码登录功能，支持 SSE 实时状态推送
 */
import { useState, useCallback, useEffect, useRef } from 'react'
import { Modal, Form, Input, Button, Space, message, Progress } from 'antd'
import axios from 'axios'
import { useQueryClient } from '@tanstack/react-query'

interface LoginModalProps {
  accountId: number
  accountName: string
  open: boolean
  onSuccess: () => void
  onCancel: () => void
}

interface LoginRequest {
  phone: string
  code: string
}

interface LoginResponse {
  success: boolean
  message: string
  status: string
  storage_state?: string
}

// SSE 状态枚举 (与后端 LoginStatus 一致)
type LoginStatus = 'idle' | 'waiting_phone' | 'code_sent' | 'waiting_verify' | 'verifying' | 'success' | 'error'

// SSE 状态事件数据
interface StatusUpdateEvent {
  status: LoginStatus
  message: string
  progress?: number
}

// SSE 完成事件数据
interface DoneEvent {
  final_status: 'success' | 'error'
  message?: string
}

// 状态消息映射
const STATUS_MESSAGES: Record<LoginStatus, string> = {
  idle: '',
  waiting_phone: '等待输入手机号...',
  waiting_verify: '等待输入验证码...',
  code_sent: '验证码已发送，请输入',
  verifying: '正在验证...',
  success: '登录成功！',
  error: '登录失败',
}

const COUNTDOWN_SECONDS = 60

export default function LoginModal({
  accountId,
  accountName,
  open,
  onSuccess,
  onCancel,
}: LoginModalProps) {
  const [form] = Form.useForm<LoginRequest>()
  const [countdown, setCountdown] = useState(0)
  const [loading, setLoading] = useState(false)
  const [sendLoading, setSendLoading] = useState(false)

  // SSE 状态
  const [statusMessage, setStatusMessage] = useState('')
  const [progress, setProgress] = useState(0)
  const eventSourceRef = useRef<EventSource | null>(null)
  const queryClient = useQueryClient()

  // 订阅 SSE 状态更新
  useEffect(() => {
    if (!open) {
      // Modal 关闭时清理 SSE 连接
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      return
    }

    // 重置 SSE 状态
    setStatusMessage('')
    setProgress(0)

    // 创建 SSE 连接
    const eventSource = new EventSource(`/api/accounts/login/${accountId}/stream`)
    eventSourceRef.current = eventSource

    // 监听状态更新事件
    eventSource.addEventListener('status_update', (e: MessageEvent) => {
      try {
        const data: StatusUpdateEvent = JSON.parse(e.data)
        const message = data.message || STATUS_MESSAGES[data.status] || ''
        setStatusMessage(message)
        setProgress(data.progress ?? 0)
      } catch (err) {
        console.error('Failed to parse SSE status_update event:', err)
      }
    })

    // 监听完成事件
    eventSource.addEventListener('done', (e: MessageEvent) => {
      try {
        const data: DoneEvent = JSON.parse(e.data)
        if (data.final_status === 'success') {
          message.success('登录成功')
          queryClient.invalidateQueries({ queryKey: ['accounts'] })
          onSuccess()
        } else {
          message.error(data.message || '登录失败')
        }
        eventSource.close()
        eventSourceRef.current = null
      } catch (err) {
        console.error('Failed to parse SSE done event:', err)
      }
    })

    // 错误处理
    eventSource.onerror = () => {
      console.error('SSE connection error')
      eventSource.close()
      eventSourceRef.current = null
    }

    // 清理函数
    return () => {
      eventSource.close()
      eventSourceRef.current = null
    }
  }, [open, accountId, onSuccess, queryClient])

  // 倒计时效果
  useEffect(() => {
    if (countdown <= 0) return

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [countdown > 0])

  // 重置表单和状态
  useEffect(() => {
    if (!open) {
      form.resetFields()
      setCountdown(0)
      setLoading(false)
      setSendLoading(false)
      setStatusMessage('')
      setProgress(0)
    }
  }, [open, form])

  // 发送验证码 - 触发后端发送短信验证码
  const handleSendCode = useCallback(async () => {
    const phone = form.getFieldValue('phone')

    // 验证手机号格式
    if (!phone || !/^1\d{10}$/.test(phone)) {
      message.error('请输入正确的手机号')
      return
    }

    setSendLoading(true)
    try {
      // 发送验证码请求
      // 注意：这里使用单独的发送验证码接口，如果没有则需要后端支持
      // 当前实现：调用登录接口但只传手机号，由后端处理发送验证码逻辑
      await axios.post(`/api/accounts/login/${accountId}`, {
        phone,
        code: '', // 空验证码表示只发送
      })

      message.success('验证码已发送')
      setCountdown(COUNTDOWN_SECONDS)
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        message.error(error.response?.data?.detail || '发送验证码失败')
      } else if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('发送验证码失败')
      }
    } finally {
      setSendLoading(false)
    }
  }, [accountId, form])

  // 登录提交
  const handleLogin = async (values: LoginRequest) => {
    setLoading(true)
    try {
      const response = await axios.post<LoginResponse>(
        `/api/accounts/login/${accountId}`,
        {
          phone: values.phone,
          code: values.code,
        }
      )

      const data = response.data

      if (data.success) {
        message.success(data.message || '登录成功')
        // 刷新账号列表
        queryClient.invalidateQueries({ queryKey: ['accounts'] })
        onSuccess()
      } else {
        message.error(data.message || '登录失败')
      }
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        message.error(error.response?.data?.detail || '登录失败')
      } else if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('登录失败')
      }
    } finally {
      setLoading(false)
    }
  }

  // 表单验证规则
  const phoneRules = [
    { required: true, message: '请输入手机号' },
    { pattern: /^1\d{10}$/, message: '手机号格式不正确' },
  ]

  const codeRules = [
    { required: true, message: '请输入验证码' },
    { min: 4, max: 6, message: '验证码长度为4-6位' },
  ]

  return (
    <Modal
      title={`登录账号: ${accountName}`}
      open={open}
      onCancel={onCancel}
      footer={null}
      destroyOnClose
      maskClosable={!loading}
      closable={!loading}
    >
      {/* SSE 状态显示 */}
      {statusMessage && (
        <div
          style={{
            marginBottom: 16,
            padding: 12,
            background: '#f5f5f5',
            borderRadius: 4,
            border: '1px solid #d9d9d9',
          }}
        >
          <div style={{ marginBottom: progress > 0 ? 8 : 0 }}>{statusMessage}</div>
          {progress > 0 && <Progress percent={progress} size="small" status="active" />}
        </div>
      )}

      <Form
        form={form}
        layout="vertical"
        onFinish={handleLogin}
        autoComplete="off"
      >
        <Form.Item
          name="phone"
          label="手机号"
          rules={phoneRules}
          extra="请输入得物账号绑定的手机号"
        >
          <Input
            placeholder="请输入手机号"
            maxLength={11}
            disabled={loading}
          />
        </Form.Item>

        <Form.Item label="验证码">
          <Space.Compact style={{ width: '100%' }}>
            <Form.Item
              name="code"
              noStyle
              rules={codeRules}
              dependencies={['phone']}
            >
              <Input
                placeholder="请输入验证码"
                maxLength={6}
                style={{ width: '60%' }}
                disabled={loading}
              />
            </Form.Item>
            <Button
              onClick={handleSendCode}
              disabled={countdown > 0 || sendLoading}
              loading={sendLoading}
              style={{ width: '40%' }}
            >
              {countdown > 0 ? `${countdown}秒后重发` : '获取验证码'}
            </Button>
          </Space.Compact>
        </Form.Item>

        <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={onCancel} disabled={loading}>
              取消
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
            >
              登录
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  )
}
