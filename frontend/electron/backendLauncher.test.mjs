import test from 'node:test'
import assert from 'node:assert/strict'
import { EventEmitter } from 'node:events'

import {
  BackendStartupError,
  createBackendLauncherSpec,
  waitForBackendHealth,
} from './backendLauncher.ts'

class FakeChild extends EventEmitter {
  removeListener(eventName, listener) {
    return super.removeListener(eventName, listener)
  }
}

test('createBackendLauncherSpec exposes health URL and command contract', () => {
  const spec = createBackendLauncherSpec({
    isDev: true,
    electronDir: '/repo/frontend/electron',
    platform: 'linux',
    resourcesPath: '/resources',
  })

  assert.equal(spec.command, 'bash')
  assert.equal(spec.healthUrl, 'http://127.0.0.1:8000/health')
  assert.equal(spec.env.BACKEND_PORT, '8000')
})

test('waitForBackendHealth resolves when health endpoint becomes healthy', async () => {
  const child = new FakeChild()
  let attempts = 0

  await waitForBackendHealth(child, 'http://localhost/health', {
    timeoutMs: 1000,
    retryIntervalMs: 1,
    sleep: async () => {},
    fetchImpl: async () => {
      attempts += 1
      if (attempts < 2) {
        throw new Error('not ready')
      }
      return {
        ok: true,
        json: async () => ({ status: 'healthy' }),
      }
    },
  })

  assert.equal(attempts, 2)
})

test('waitForBackendHealth fails on early process exit', async () => {
  const child = new FakeChild()

  const promise = waitForBackendHealth(child, 'http://localhost/health', {
    timeoutMs: 1000,
    retryIntervalMs: 1,
    sleep: async () => {},
    fetchImpl: async () => ({ ok: false, json: async () => ({}) }),
  })

  child.emit('exit', 1, null)

  await assert.rejects(promise, (error) => {
    assert.ok(error instanceof BackendStartupError)
    assert.equal(error.code, 'early_exit')
    return true
  })
})

test('waitForBackendHealth times out when health never stabilizes', async () => {
  const child = new FakeChild()

  await assert.rejects(
    waitForBackendHealth(child, 'http://localhost/health', {
      timeoutMs: 5,
      retryIntervalMs: 1,
      sleep: async () => new Promise((resolve) => setTimeout(resolve, 2)),
      fetchImpl: async () => ({ ok: false, json: async () => ({}) }),
    }),
    (error) => {
      assert.ok(error instanceof BackendStartupError)
      assert.equal(error.code, 'health_timeout')
      return true
    },
  )
})
