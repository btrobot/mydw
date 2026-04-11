#!/usr/bin/env node

/**
 * DewuGoJin CLI - 得物掘金工具 API 测试 CLI
 * 主入口文件
 */

import { ok, fail, info, C } from './utils/output.js'
import { GET } from './utils/http.js'
import { handleAccountCommand } from './commands/account.js'
import { handleConnectionCommand } from './commands/connection.js'
import { handleHttpCommand } from './commands/http.js'
import {
  runAccountTests,
  runTaskTests,
  runMaterialTests,
  TestResult,
} from './suites/index.js'
import { VERSION } from './version.js'

// 帮助信息
const HELP = `
${C.bold('DewuGoJin CLI')} - 得物掘金工具 API 测试 CLI

${C.yellow('用法:')} dewu-cli <command> [args...]

${C.yellow('账号管理:')}
  account list              列出得物账号
  account add <id> <name>   添加账号
  account remove <id>       删除账号
  account status <id>       查看账号状态
  account stats             查看统计信息

${C.yellow('连接管理:')}
  connect <id> [--phone <phone>]  建立连接
  disconnect <id>           断开连接
  status <id>               查看连接状态

${C.yellow('HTTP 请求:')}
  get <path>                GET 请求
  post <path> [json]        POST 请求
  put <path> [json]         PUT 请求
  delete <path>             DELETE 请求

${C.yellow('测试套件:')}
  test accounts             测试账号 API
  test tasks                测试任务 API
  test materials            测试素材 API
  test all                  测试所有 API

${C.yellow('系统:')}
  health                    后端健康检查
  --help, -h                显示帮助
  --version, -v             显示版本

${C.yellow('示例:')}
  dewu-cli account list
  dewu-cli connect 1 --phone 13800138000
  dewu-cli test all
  dewu-cli get /api/accounts
`

async function main(): Promise<void> {
  const args = process.argv.slice(2)
  const cmd = args[0]

  if (!cmd || cmd === '--help' || cmd === '-h') {
    console.log(HELP)
    return
  }

  if (cmd === '--version' || cmd === '-v') {
    console.log(`dewu-cli ${VERSION}`)
    return
  }

  switch (cmd) {
    case 'health':
      await cmdHealth()
      break

    // 账号管理命令
    case 'account':
      await handleAccountCommand(args)
      break

    // 连接管理命令
    case 'connect':
    case 'disconnect':
    case 'status':
      await handleConnectionCommand(args)
      break

    // 测试命令
    case 'test':
      await cmdTest(args[1])
      break

    // HTTP 请求命令
    case 'get':
      await handleHttpCommand('get', args.slice(1))
      break

    case 'post':
      await handleHttpCommand('post', args.slice(1))
      break

    case 'put':
      await handleHttpCommand('put', args.slice(1))
      break

    case 'delete':
      await handleHttpCommand('delete', args.slice(1))
      break

    default:
      fail(`未知命令: ${cmd}`)
      info(`执行 ${C.cyan('dewu-cli --help')} 查看可用命令`)
  }
}

/**
 * 后端健康检查
 */
async function cmdHealth(): Promise<void> {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:8000'
  info(`检查后端健康状态: ${BASE_URL}/health`)
  try {
    const res = await GET('/health')
    if (res.code === 0 || res.code === 200) {
      ok('后端正常')
    } else {
      fail(`后端异常: code=${res.code}`)
    }
  } catch (e) {
    fail(`后端不可达: ${(e as Error).message}`)
    process.exit(1)
  }
}

/**
 * 运行测试套件
 */
async function cmdTest(domain?: string): Promise<void> {
  if (!domain) {
    fail('缺少 domain 参数')
    info('可用 domain: accounts, tasks, materials, all')
    return
  }

  const totalResult: TestResult = {
    passed: 0,
    failed: 0,
    total: 0,
  }

  const runAndAccumulate = async (
    testFn: () => Promise<TestResult>,
    domainName: string
  ): Promise<void> => {
    console.log('')
    console.log(C.bold(`=== 测试域: ${domainName} ===`))
    const result = await testFn()
    totalResult.passed += result.passed
    totalResult.failed += result.failed
    totalResult.total += result.total
  }

  switch (domain) {
    case 'accounts':
      await runAndAccumulate(runAccountTests, 'accounts')
      break

    case 'tasks':
      await runAndAccumulate(runTaskTests, 'tasks')
      break

    case 'materials':
      await runAndAccumulate(runMaterialTests, 'materials')
      break

    case 'all':
      await runAndAccumulate(runAccountTests, 'accounts')
      await runAndAccumulate(runTaskTests, 'tasks')
      await runAndAccumulate(runMaterialTests, 'materials')
      break

    default:
      fail(`未知 domain: ${domain}`)
      info('可用 domain: accounts, tasks, materials, all')
      return
  }

  // 打印总计
  console.log('')
  console.log(C.bold('--- 总计 ---'))
  console.log(`${C.green('✓ 通过')}: ${totalResult.passed}`)
  console.log(`${C.red('✗ 失败')}: ${totalResult.failed}`)
  console.log(`${C.dim('总计')}: ${totalResult.total}`)

  if (totalResult.failed > 0) {
    process.exit(1)
  }
}

main().catch((e) => {
  fail(`错误: ${e.message}`)
  process.exit(1)
})
