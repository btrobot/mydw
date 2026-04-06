/**
 * ConnectionModal - 得物账号连接弹窗组件
 *
 * 提供手机验证码连接功能，支持 SSE 实时状态推送
 */
import { useState, useCallback, useEffect, useRef } from 'react'
import { Modal, Form, Input, Button, Space, message, Progress, Alert, Switch } from 'antd'
import axios from 'axios'
import { useQueryClient } from '@tanstack/react-query'

interface ConnectionModalProps {
  accountId: number
  accountName: string
  phoneMasked?: string | null
  open: boolean
  onSuccess: () => void
  onCancel: () => void
}

// 表单字段 — phone is optional when using stored number
interface FormValues {
  phone?: string
  code: string
}

// send-code 端点请求体
interface SendCodeRequest {
  phone?: string
}

// verify 端点请求体
interface VerifyCodeRequest {
  code: string
}

// verify 端点响应体
interface VerifyCodeResponse {
  success: boolean
  message: string
  status: string
}

// SSE 状态枚举 (与后端 ConnectionStatus 一致)
type ConnectionStatus = 'idle' | 'waiting_phone' | 'code_sent' | 'waiting_verify' | 'verifying' | 'success' | 'error'

// SSE 状态事件数据
interface StatusUpdateEvent {
  status: ConnectionStatus
  message: string
  progress?: number
}

// SSE 完成事件数据
interface DoneEvent {
  final_status: 'success' | 'error'
  message?: string
}

// 状态消息映射
const STATUS_MESSAGES: Record<ConnectionStatus, string> = {
  idle: '',
  waiting_phone: '等待输入手机号...',
  waiting_verify: '等待输入验证码...',
  code_sent: '验证码已发送，请输入',
  verifying: '正在验证...',
  success: '连接成功！',
  error: '连接失败',
}

const COUNTDOWN_SECONDS = 60

export default function ConnectionModal({
  accountId,
  accountName,
  phoneMasked,
  open,
  onSuccess,
  onCancel,
}: ConnectionModalProps) {
  const [form] = Form.useForm<FormValues>()
  const [countdown, setCountdown] = useState(0)
  const [loading, setLoading] = useState(false)
  const [sendLoading, setSendLoading] = useState(false)

  // 使用已存储手机号的开关 — 仅在有存储手机号时有效
  const hasStoredPhone = Boolean(phoneMasked)
  const [useStoredPhone, setUseStoredPhone] = useState(hasStoredPhone)

  // SSE 状态
  const [statusMessage, setStatusMessage] = useState('')
  const [progress, setProgress] = useState(0)
  const [connectionError, setConnectionError] = useState(false)
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
    const eventSource = new EventSource(`/api/accounts/connect/${accountId}/stream`)
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
    eventSource.addEventListener('done', async (e: MessageEvent) => {
      try {
        const data: DoneEvent = JSON.parse(e.data)
        if (data.final_status === 'success') {
          message.success('连接成功')
          await queryClient.invalidateQueries({ queryKey: ['accounts'] })
          onSuccess()
        } else {
          message.error(data.message || '连接失败')
        }
        eventSource.close()
        eventSourceRef.current = null
      } catch (err) {
        console.error('Failed to parse SSE done event:', err)
      }
    })

    // 错误处理
    eventSource.onerror = (e: Event) => {
      console.error('SSE connection error:', e)
      setStatusMessage('连接状态服务器失败，请检查网络')
      setConnectionError(true)
      // 30秒后自动重连
      setTimeout(() => {
        if (eventSourceRef.current === eventSource) {
          eventSource.close()
          eventSourceRef.current = null
          setConnectionError(false)
        }
      }, 30000)
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
      setConnectionError(false)
      // 重新打开时恢复默认：有存储号码则默认使用
      setUseStoredPhone(Boolean(phoneMasked))
    }
  }, [open, form, phoneMasked])

  // 发送验证码 - 触发后端发送短信验证码
  const handleSendCode = useCallback(async () => {
    // 使用已存储手机号时跳过前端格式验证
    if (!useStoredPhone) {
      const phone = form.getFieldValue('phone') as string | undefined

      // 验证手机号格式
      if (!phone || !/^1\d{10}$/.test(phone)) {
        message.error('请输入正确的手机号')
        return
      }
    }

    setSendLoading(true)
    try {
      const body: SendCodeRequest = useStoredPhone
        ? {}
        : { phone: form.getFieldValue('phone') as string }

      await axios.post(`/api/accounts/connect/${accountId}/send-code`, body)

      message.success('验证码已发送')
      setCountdown(COUNTDOWN_SECONDS)
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        const status = error.response?.status
        if (status === 409) {
          message.warning(error.response?.data?.detail || '账号正在连接中，请稍候')
        } else {
          message.error(error.response?.data?.detail || '发送验证码失败')
        }
      } else if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('发送验证码失败')
      }
    } finally {
      setSendLoading(false)
    }
  }, [accountId, form, useStoredPhone])

  // 连接提交
  const handleConnect = async (values: FormValues) => {
    setLoading(true)
    try {
      const body: VerifyCodeRequest = { code: values.code }
      const response = await axios.post<VerifyCodeResponse>(
        `/api/accounts/connect/${accountId}/verify`,
        body
      )

      const data = response.data

      if (data.success) {
        // 成功路径：SSE 的 done 事件会负责关闭弹窗和刷新列表
        // 此处不再重复调用 onSuccess，避免竞争
      } else {
        message.error(data.message || '验证码错误或已过期，请重新获取')
      }
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        const status = error.response?.status
        if (status === 422) {
          message.error(error.response?.data?.detail || '请先发送验证码')
        } else {
          message.error(error.response?.data?.detail || '连接失败')
        }
      } else if (error instanceof Error) {
        message.error(error.message)
      } else {
        message.error('连接失败')
      }
    } finally {
      setLoading(false)
    }
  }

  // 表单验证规则
  const phoneRules = useStoredPhone
    ? []
    : [
        { required: true, message: '请输入手机号' },
        { pattern: /^1\d{10}$/, message: '手机号格式不正确' },
      ]

  const codeRules = [
    { required: true, message: '请输入验证码' },
    { min: 4, max: 6, message: '验证码长度为4-6位' },
  ]

  return (
    <Modal
      title={`建立连接: ${accountName}`}
      open={open}
      onCancel={onCancel}
      footer={null}
      destroyOnClose
      maskClosable={!loading}
      closable={!loading}
    >
      {/* SSE 状态显示 */}
      {connectionError ? (
        <Alert
          type="error"
          message="连接已断开，正在尝试重连..."
          showIcon
          style={{ marginBottom: 16 }}
        />
      ) : statusMessage ? (
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
      ) : null}

      <Form
        form={form}
        layout="vertical"
        onFinish={handleConnect}
        autoComplete="off"
      >
        {/* 使用已存储手机号开关 — 仅在有存储号码时显示 */}
        {hasStoredPhone && (
          <Form.Item style={{ marginBottom: 12 }}>
            <Space>
              <Switch
                checked={useStoredPhone}
                onChange={setUseStoredPhone}
                disabled={loading}
                size="small"
              />
              <span style={{ color: '#595959' }}>
                使用已存储的手机号（{phoneMasked}）
              </span>
            </Space>
          </Form.Item>
        )}

        <Form.Item
          name="phone"
          label="手机号"
          rules={phoneRules}
          extra={useStoredPhone ? undefined : '请输入得物账号绑定的手机号'}
        >
          <Input
            placeholder={
              useStoredPhone
                ? `${phoneMasked ?? ''}，留空使用已存储号码`
                : '请输入手机号'
            }
            maxLength={11}
            disabled={loading || useStoredPhone}
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
              连接
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  )
}
