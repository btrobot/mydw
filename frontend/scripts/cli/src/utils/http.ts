/**
 * HTTP 请求封装工具
 * 提供 GET/POST/PUT/DELETE 方法
 */

export interface HttpResponse {
  code: number
  message?: string
  data: unknown
}

/**
 * 标准化 URL 路径 (Windows 兼容处理)
 * 将 Windows 路径转换为标准 URL 路径
 */
function normalizeUrlPath(path: string): string {
  // 移除 Drive 盘符前缀 (C:, D:, etc)
  const driveMatch = path.match(/^[A-Za-z]:(.*)$/)
  if (driveMatch) {
    path = driveMatch[1]
  }
  // 确保路径以 / 开头
  if (!path.startsWith('/')) {
    path = '/' + path
  }
  return path
}

export async function httpRequest(
  method: string,
  urlPath: string,
  body?: unknown,
  params?: Record<string, string>
): Promise<HttpResponse> {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:8000'
  const normalizedPath = normalizeUrlPath(urlPath)
  let url = `${BASE_URL}${normalizedPath}`
  if (params) {
    const qs = Object.entries(params)
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
      .join('&')
    if (qs) url += `?${qs}`
  }

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }

  const init: RequestInit = { method: method.toUpperCase(), headers }
  if (body !== undefined && method !== 'GET') {
    init.body = JSON.stringify(body)
  }

  const res = await fetch(url, init)
  const text = await res.text()

  if (!res.ok && !text) {
    return { code: res.status, message: `HTTP ${res.status}`, data: null }
  }
  try {
    return JSON.parse(text)
  } catch {
    return { code: res.status, message: text.slice(0, 200), data: null }
  }
}

export const GET = (p: string, params?: Record<string, string>) => httpRequest('GET', p, undefined, params)
export const POST = (p: string, body?: unknown) => httpRequest('POST', p, body)
export const PUT = (p: string, body?: unknown) => httpRequest('PUT', p, body)
export const DELETE = (p: string, body?: unknown) => httpRequest('DELETE', p, body)
