/**
 * 通用 HTTP 命令
 * 实现 RESTful API 调用 (GET/POST/PUT/DELETE)
 */

import { GET, POST, PUT, DELETE } from '../utils/http.js'
import { ok, fail, info } from '../utils/output.js'

// API 响应类型
interface ApiResponse {
  code: number
  message?: string
  data?: unknown
}

/**
 * 执行 GET 请求
 * @param path API 路径
 */
export async function handleGet(path: string): Promise<void> {
  if (!path) {
    fail('缺少 path 参数')
    info('用法: dewu-cli get <path>')
    return
  }

  info(`GET ${path}`)
  try {
    const res = await GET(path) as ApiResponse
    printApiResult(res)
  } catch (e) {
    fail(`请求失败: ${(e as Error).message}`)
  }
}

/**
 * 执行 POST 请求
 * @param path API 路径
 * @param json 可选的 JSON body
 */
export async function handlePost(path: string, json?: string): Promise<void> {
  if (!path) {
    fail('缺少 path 参数')
    info('用法: dewu-cli post <path> [json]')
    return
  }

  let body: unknown = undefined
  if (json) {
    try {
      body = JSON.parse(json)
    } catch {
      fail(`无效的 JSON: ${json}`)
      return
    }
  }

  info(`POST ${path}`)
  if (body) {
    info(`Body: ${JSON.stringify(body)}`)
  }

  try {
    const res = await POST(path, body) as ApiResponse
    printApiResult(res)
  } catch (e) {
    fail(`请求失败: ${(e as Error).message}`)
  }
}

/**
 * 执行 PUT 请求
 * @param path API 路径
 * @param json 可选的 JSON body
 */
export async function handlePut(path: string, json?: string): Promise<void> {
  if (!path) {
    fail('缺少 path 参数')
    info('用法: dewu-cli put <path> [json]')
    return
  }

  let body: unknown = undefined
  if (json) {
    try {
      body = JSON.parse(json)
    } catch {
      fail(`无效的 JSON: ${json}`)
      return
    }
  }

  info(`PUT ${path}`)
  if (body) {
    info(`Body: ${JSON.stringify(body)}`)
  }

  try {
    const res = await PUT(path, body) as ApiResponse
    printApiResult(res)
  } catch (e) {
    fail(`请求失败: ${(e as Error).message}`)
  }
}

/**
 * 执行 DELETE 请求
 * @param path API 路径
 */
export async function handleDelete(path: string): Promise<void> {
  if (!path) {
    fail('缺少 path 参数')
    info('用法: dewu-cli delete <path>')
    return
  }

  info(`DELETE ${path}`)
  try {
    const res = await DELETE(path) as ApiResponse
    printApiResult(res)
  } catch (e) {
    fail(`请求失败: ${(e as Error).message}`)
  }
}

/**
 * 打印 API 结果
 */
function printApiResult(res: ApiResponse): void {
  const code = res.code ?? 0
  if (code === 0 || code === 200) {
    ok('success')
    const data = res.data ?? res
    if (data === null || data === undefined) return
    console.log(JSON.stringify(data, null, 2))
  } else {
    fail(`code=${code} ${res.message || ''}`)
    if (res.data) {
      console.log(JSON.stringify(res.data, null, 2))
    }
  }
}

/**
 * 处理 HTTP 命令路由
 */
export async function handleHttpCommand(
  method: 'get' | 'post' | 'put' | 'delete',
  args: string[]
): Promise<void> {
  const path = args[0]
  const json = args[1]

  switch (method) {
    case 'get':
      await handleGet(path)
      break
    case 'post':
      await handlePost(path, json)
      break
    case 'put':
      await handlePut(path, json)
      break
    case 'delete':
      await handleDelete(path)
      break
  }
}
