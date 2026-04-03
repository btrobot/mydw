/**
 * 账号管理命令
 * 实现得物账号的 CRUD 操作
 */

import { GET, POST, DELETE } from '../utils/http.js'
import { ok, fail, info, warn } from '../utils/output.js'

// API 响应类型
interface AccountResponse {
  code: number
  message?: string
  data?: Account[] | Account | null
}

interface Account {
  id: number
  account_id: string
  account_name: string
  status: string
  created_at?: string
  updated_at?: string
}

interface StatsResponse {
  code: number
  message?: string
  data?: {
    total: number
    active: number
    inactive: number
  }
}

/**
 * 格式化账号状态
 */
function formatStatus(status: string): string {
  const statusMap: Record<string, string> = {
    active: 'active',
    inactive: 'inactive',
    connected: 'connected',
    disconnected: 'disconnected',
  }
  return statusMap[status.toLowerCase()] || status
}

/**
 * 列出所有得物账号
 */
export async function listAccounts(): Promise<void> {
  info('获取账号列表...')
  try {
    const res = await GET('/api/accounts')
    const response = res as AccountResponse

    if (response.code === 0 || response.code === 200) {
      ok('账号列表:')
      const accounts = response.data as Account[]

      if (!accounts || accounts.length === 0) {
        warn('  没有账号')
        return
      }

      for (const account of accounts) {
        const statusColor = account.status === 'active' ? '\x1b[32m' : '\x1b[2m'
        console.log(
          `  [\x1b[36m${account.id}\x1b[0m] ${account.account_id} - ${account.account_name} - ${statusColor}${formatStatus(account.status)}\x1b[0m`
        )
      }
    } else {
      fail(`获取账号列表失败: code=${response.code} ${response.message || ''}`)
    }
  } catch (e) {
    fail(`获取账号列表失败: ${(e as Error).message}`)
  }
}

/**
 * 添加得物账号
 */
export async function addAccount(accountId: string, name: string): Promise<void> {
  if (!accountId || !name) {
    fail('缺少必要参数')
    info('用法: dewu-cli account add <account_id> <name>')
    return
  }

  info(`添加账号: ${accountId} (${name})...`)
  try {
    const res = await POST('/api/accounts', {
      account_id: accountId,
      account_name: name,
    })
    const response = res as AccountResponse

    if (response.code === 0 || response.code === 200) {
      ok('账号添加成功')
      console.log(JSON.stringify(response.data, null, 2))
    } else {
      fail(`添加失败: code=${response.code} ${response.message || ''}`)
    }
  } catch (e) {
    fail(`添加账号失败: ${(e as Error).message}`)
  }
}

/**
 * 删除得物账号
 */
export async function removeAccount(id: string): Promise<void> {
  if (!id) {
    fail('缺少 id 参数')
    info('用法: dewu-cli account remove <id>')
    return
  }

  info(`删除账号 ID: ${id}...`)
  try {
    const res = await DELETE(`/api/accounts/${id}`)
    const response = res as AccountResponse

    if (response.code === 0 || response.code === 200) {
      ok('账号删除成功')
    } else {
      fail(`删除失败: code=${response.code} ${response.message || ''}`)
    }
  } catch (e) {
    fail(`删除账号失败: ${(e as Error).message}`)
  }
}

/**
 * 查看账号详情
 */
export async function getAccountStatus(id: string): Promise<void> {
  if (!id) {
    fail('缺少 id 参数')
    info('用法: dewu-cli account status <id>')
    return
  }

  info(`查看账号 ${id} 详情...`)
  try {
    const res = await GET(`/api/accounts/${id}`)
    const response = res as AccountResponse

    if (response.code === 0 || response.code === 200) {
      ok('账号详情:')
      const account = response.data as Account
      console.log(JSON.stringify(account, null, 2))
    } else {
      fail(`获取详情失败: code=${response.code} ${response.message || ''}`)
    }
  } catch (e) {
    fail(`获取账号详情失败: ${(e as Error).message}`)
  }
}

/**
 * 获取账号统计信息
 */
export async function getAccountStats(): Promise<void> {
  info('获取账号统计...')
  try {
    const res = await GET('/api/accounts/stats')
    const response = res as StatsResponse

    if (response.code === 0 || response.code === 200) {
      ok('账号统计:')
      const stats = response.data
      console.log(`  总计: ${stats?.total || 0}`)
      console.log(`  \x1b[32m活跃\x1b[0m: ${stats?.active || 0}`)
      console.log(`  \x1b[2m离线\x1b[0m: ${stats?.inactive || 0}`)
    } else {
      fail(`获取统计失败: code=${response.code} ${response.message || ''}`)
    }
  } catch (e) {
    fail(`获取统计失败: ${(e as Error).message}`)
  }
}

/**
 * 处理 account 命令路由
 */
export async function handleAccountCommand(args: string[]): Promise<void> {
  const [action, ...restArgs] = args.slice(1) // 跳过 'account'

  if (!action) {
    warn('缺少 action 参数')
    info('可用 action: list, add, remove, status, stats')
    return
  }

  switch (action) {
    case 'list':
      await listAccounts()
      break

    case 'add':
      await addAccount(restArgs[0], restArgs[1])
      break

    case 'remove':
      await removeAccount(restArgs[0])
      break

    case 'status':
      await getAccountStatus(restArgs[0])
      break

    case 'stats':
      await getAccountStats()
      break

    default:
      fail(`未知 action: ${action}`)
      info('可用 action: list, add, remove, status, stats')
  }
}
