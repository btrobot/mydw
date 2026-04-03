/**
 * 素材 API 测试套件
 * 测试素材相关 API
 */

import { GET } from '../utils/http.js'
import { ok, fail, C } from '../utils/output.js'

// API 响应类型
interface ApiResponse {
  code: number
  message?: string
  data?: unknown
}

// 测试用例接口
export interface TestCase {
  name: string
  fn: () => Promise<ApiResponse>
}

export interface TestResult {
  passed: number
  failed: number
  total: number
}

/**
 * 获取素材测试用例
 */
export function getMaterialTests(): TestCase[] {
  return [
    {
      name: 'GET /api/materials/ (素材列表)',
      fn: () => GET('/api/materials'),
    },
    {
      name: 'GET /api/materials/stats (统计)',
      fn: () => GET('/api/materials/stats'),
    },
  ]
}

/**
 * 运行素材测试
 */
export async function runMaterialTests(): Promise<TestResult> {
  const tests = getMaterialTests()
  let passed = 0
  let failed = 0

  for (const t of tests) {
    try {
      const res = await t.fn()
      if (res.code === 0 || res.code === 200) {
        ok(t.name)
        passed++
      } else {
        fail(`${t.name} → code=${res.code}`)
        failed++
      }
    } catch (e) {
      fail(`${t.name} → ${(e as Error).message}`)
      failed++
    }
  }

  return { passed, failed, total: tests.length }
}

/**
 * 打印测试结果摘要
 */
export function printTestSummary(result: TestResult, domain: string): void {
  console.log('')
  console.log(`${C.bold('--- ' + domain + ' 测试结果 ---')}`)
  console.log(`${C.green('✓ 通过')}: ${result.passed}`)
  console.log(`${C.red('✗ 失败')}: ${result.failed}`)
  console.log(`${C.dim('总计')}: ${result.total}`)
}
