import path from 'path'
import type { ChildProcess } from 'child_process'

export interface BackendLauncherOptions {
  isDev: boolean
  electronDir: string
  resourcesPath?: string
  host?: string
  port?: number
  platform?: NodeJS.Platform
}

export interface BackendLauncherSpec {
  backendPath: string
  command: string
  args: string[]
  cwd: string
  env: NodeJS.ProcessEnv
  healthUrl: string
}

export type BackendStartupFailureCode = 'spawn_failure' | 'early_exit' | 'health_timeout'

export class BackendStartupError extends Error {
  code: BackendStartupFailureCode

  constructor(code: BackendStartupFailureCode, message: string) {
    super(message)
    this.name = 'BackendStartupError'
    this.code = code
  }
}

export interface WaitForBackendHealthOptions {
  timeoutMs?: number
  retryIntervalMs?: number
  fetchImpl?: typeof fetch
  sleep?: (ms: number) => Promise<void>
}

const DEFAULT_HOST = '127.0.0.1'
const DEFAULT_PORT = 8000
const DEFAULT_TIMEOUT_MS = 15_000
const DEFAULT_RETRY_MS = 500

function resolveBackendRoot(options: BackendLauncherOptions): string {
  if (options.isDev) {
    return path.resolve(options.electronDir, '../../backend')
  }

  return path.join(options.resourcesPath ?? '', 'backend')
}

function resolveLauncherPath(options: BackendLauncherOptions): string {
  const launcherName = options.isDev ? 'start-backend-dev' : 'start-backend-prod'
  const extension = (options.platform ?? process.platform) === 'win32' ? '.bat' : '.sh'
  return path.resolve(options.electronDir, 'launchers', `${launcherName}${extension}`)
}

export function createBackendLauncherSpec(options: BackendLauncherOptions): BackendLauncherSpec {
  const platform = options.platform ?? process.platform
  const host = options.host ?? DEFAULT_HOST
  const port = options.port ?? DEFAULT_PORT
  const backendPath = resolveBackendRoot(options)
  const launcherPath = resolveLauncherPath(options)

  if (platform === 'win32') {
    return {
      backendPath,
      command: 'cmd.exe',
      args: ['/d', '/s', '/c', launcherPath, backendPath, host, String(port)],
      cwd: backendPath,
      env: { ...process.env, BACKEND_ROOT: backendPath, BACKEND_HOST: host, BACKEND_PORT: String(port) },
      healthUrl: `http://${host}:${port}/health`,
    }
  }

  return {
    backendPath,
    command: 'bash',
    args: [launcherPath, backendPath, host, String(port)],
    cwd: backendPath,
    env: { ...process.env, BACKEND_ROOT: backendPath, BACKEND_HOST: host, BACKEND_PORT: String(port) },
    healthUrl: `http://${host}:${port}/health`,
  }
}

export async function waitForBackendHealth(
  child: Pick<ChildProcess, 'once' | 'removeListener'>,
  healthUrl: string,
  options: WaitForBackendHealthOptions = {},
): Promise<void> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const retryIntervalMs = options.retryIntervalMs ?? DEFAULT_RETRY_MS
  const fetchImpl = options.fetchImpl ?? fetch
  const sleep = options.sleep ?? ((ms: number) => new Promise((resolve) => setTimeout(resolve, ms)))
  const startedAt = Date.now()

  let earlyExitMessage: string | null = null
  let spawnErrorMessage: string | null = null

  const onExit = (code: number | null, signal: NodeJS.Signals | null) => {
    earlyExitMessage = `Backend process exited before readiness (code=${code ?? 'null'}, signal=${signal ?? 'null'})`
  }
  const onError = (error: Error) => {
    spawnErrorMessage = `Backend launcher failed to spawn: ${error.message}`
  }

  child.once('exit', onExit)
  child.once('error', onError)

  try {
    while (Date.now() - startedAt < timeoutMs) {
      if (spawnErrorMessage !== null) {
        throw new BackendStartupError('spawn_failure', spawnErrorMessage)
      }

      if (earlyExitMessage !== null) {
        throw new BackendStartupError('early_exit', earlyExitMessage)
      }

      try {
        const response = await fetchImpl(healthUrl)
        if (response.ok) {
          const payload = (await response.json().catch(() => null)) as { status?: string } | null
          if (payload?.status === 'healthy') {
            return
          }
        }
      } catch {
        // Keep polling until success, early exit, or timeout.
      }

      await sleep(retryIntervalMs)
    }

    throw new BackendStartupError('health_timeout', `Backend did not become healthy within ${timeoutMs}ms`)
  } finally {
    child.removeListener('exit', onExit)
    child.removeListener('error', onError)
  }
}
