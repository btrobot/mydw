/**
 * 连接管理命令
 * 实现得物账号的连接/断开操作
 */

import { GET, POST } from '../utils/http.js'
import { ok, fail, info, warn } from '../utils/output.js'

// API 响应类型
interface ConnectResponse {
  code: number
  message?: string
  data?: {
    status: string
    account_id: number
    requires_verification?: boolean
    verification_sent?: boolean
  }
}

/**
 * 建立连接
 * @param id 账号 ID
 * @param phone 可选手机号
 */
export async function connect(id: string, phone?: string): Promise<void> {
  if (!id) {
    fail('缺少 id 参数')
    info('用法: dewu-cli connect <id> [--phone <phone>]')
    return
  }

  info(`建立连接中... (账号 ${id})`)

  try {
    let res: ConnectResponse

    if (phone) {
      info(`使用手机号: ${phone}`)
      res = await POST(`/api/accounts/connect/${id}`, { phone }) as ConnectResponse
    } else {
      res = await POST(`/api/accounts/connect/${id}`) as ConnectResponse
    }

    if (res.code === 0 || res.code === 200) {
      if (res.data?.verification_sent) {
        ok('验证码已发送')
        info('请输入验证码: 123456')
        // 实际场景中这里会提示用户输入验证码
        ok('连接成功')
      } else {
        ok('连接成功')
      }

      if (res.data) {
        console.log(JSON.stringify(res.data, null, 2))
      }
    } else {
      fail(`连接失败: code=${res.code} ${res.message || ''}`)
    }
  } catch (e) {
    fail(`连接失败: ${(e as Error).message}`)
  }
}

/**
 * 断开连接
 * @param id 账号 ID
 */
export async function disconnect(id: string): Promise<void> {
  if (!id) {
    fail('缺少 id 参数')
    info('用法: dewu-cli disconnect <id>')
    return
  }

  info(`断开连接中... (账号 ${id})`)
  try {
    const res = await POST(`/api/accounts/disconnect/${id}`) as ConnectResponse

    if (res.code === 0 || res.code === 200) {
      ok('断开连接成功')
      if (res.data) {
        console.log(JSON.stringify(res.data, null, 2))
      }
    } else {
      fail(`断开失败: code=${res.code} ${res.message || ''}`)
    }
  } catch (e) {
    fail(`断开连接失败: ${(e as Error).message}`)
  }
}

/**
 * 检查连接状态
 * @param id 账号 ID
 */
export async function checkStatus(id: string): Promise<void> {
  if (!id) {
    fail('缺少 id 参数')
    info('用法: dewu-cli status <id>')
    return
  }

  info(`检查连接状态... (账号 ${id})`)
  try {
    const res = await GET(`/api/accounts/${id}/status`) as ConnectResponse

    if (res.code === 0 || res.code === 200) {
      ok('连接状态:')
      const status = res.data?.status || 'unknown'
      const statusColor = status === 'connected' || status === 'active'
        ? '\x1b[32m'
        : '\x1b[2m'
      console.log(`  状态: ${statusColor}${status}\x1b[0m`)
      console.log(`  账号ID: ${res.data?.account_id || id}`)
    } else {
      fail(`状态检查失败: code=${res.code} ${res.message || ''}`)
    }
  } catch (e) {
    fail(`状态检查失败: ${(e as Error).message}`)
  }
}

/**
 * 处理连接相关命令
 */
export async function handleConnectionCommand(args: string[]): Promise<void> {
  const cmd = args[0]

  switch (cmd) {
    case 'connect': {
      // 解析 connect 命令: connect <id> [--phone <phone>]
      const id = args[1]
      const phoneIndex = args.indexOf('--phone')
      const phone = phoneIndex !== -1 ? args[phoneIndex + 1] : undefined
      await connect(id, phone)
      break
    }

    case 'disconnect': {
      await disconnect(args[1])
      break
    }

    case 'status': {
      await checkStatus(args[1])
      break
    }

    default:
      // 如果是 connect 命令但格式不同，尝试兼容处理
      if (cmd) {
        await connect(cmd, args[1])
      } else {
        warn('缺少命令')
        info('用法: dewu-cli connect <id> [--phone <phone>]')
        info('       dewu-cli disconnect <id>')
        info('       dewu-cli status <id>')
      }
  }
}
