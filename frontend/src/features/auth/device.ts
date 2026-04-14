const DEVICE_ID_STORAGE_KEY = 'mydw.auth.device_id'

export const getOrCreateDeviceId = () => {
  const existing = window.localStorage.getItem(DEVICE_ID_STORAGE_KEY)
  if (existing) {
    return existing
  }

  const created = globalThis.crypto?.randomUUID?.() ?? `device-${Date.now()}`
  window.localStorage.setItem(DEVICE_ID_STORAGE_KEY, created)
  return created
}

export const getClientVersion = async (): Promise<string> => {
  try {
    if (window.electronAPI?.getVersion) {
      return await window.electronAPI.getVersion()
    }
  } catch {
    // ignore and fall back
  }
  return 'web-dev'
}
