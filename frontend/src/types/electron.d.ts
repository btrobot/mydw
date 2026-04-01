/**
 * 得物掘金工具 - Electron 类型声明
 */

export interface ElectronAPI {
  // 系统信息
  getVersion: () => Promise<string>
  getPlatform: () => Promise<string>

  // 外部链接
  openExternal: (url: string) => Promise<void>
  openPath: (filePath: string) => Promise<void>

  // 窗口控制
  windowMinimize: () => void
  windowMaximize: () => void
  windowClose: () => void

  // 事件监听
  onPublishAction: (callback: (action: string) => void) => () => void
  removeAllListeners: (channel: string) => void
}

declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
}

export {}
