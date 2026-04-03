/**
 * 彩色控制台输出工具
 * 提供不同级别的日志输出
 */

const C = {
  green: (s: string) => `\x1b[32m${s}\x1b[0m`,
  red: (s: string) => `\x1b[31m${s}\x1b[0m`,
  yellow: (s: string) => `\x1b[33m${s}\x1b[0m`,
  cyan: (s: string) => `\x1b[36m${s}\x1b[0m`,
  dim: (s: string) => `\x1b[2m${s}\x1b[0m`,
  bold: (s: string) => `\x1b[1m${s}\x1b[0m`,
}

export function ok(msg: string): void {
  console.log(`${C.green('✓')} ${msg}`)
}

export function fail(msg: string): void {
  console.log(`${C.red('✗')} ${msg}`)
}

export function info(msg: string): void {
  console.log(`${C.cyan('ℹ')} ${msg}`)
}

export function warn(msg: string): void {
  console.log(`${C.yellow('⚠')} ${msg}`)
}

export function printResult(res: { code?: number; message?: string; data?: unknown }, label?: string): void {
  const prefix = label ? `${label}: ` : ''
  const code = res.code ?? 0
  if (code === 0 || code === 200) {
    ok(`${prefix}success`)
    const d = res.data ?? res
    if (d === null || d === undefined) return
    console.log(C.dim(JSON.stringify(d, null, 2).slice(0, 500)))
  } else {
    fail(`${prefix}code=${code} ${res.message || ''}`)
  }
}

export { C }
