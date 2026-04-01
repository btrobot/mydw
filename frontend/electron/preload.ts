/**
 * 得物掘金工具 - Preload 脚本
 * 在渲染进程和主进程之间建立安全桥接
 */
import { contextBridge, ipcRenderer } from 'electron'

// 暴露给渲染进程的 API
const electronAPI = {
  // 系统信息
  getVersion: () => ipcRenderer.invoke('get-version'),
  getPlatform: () => ipcRenderer.invoke('get-platform'),

  // 外部链接
  openExternal: (url: string) => ipcRenderer.invoke('open-external', url),
  openPath: (filePath: string) => ipcRenderer.invoke('open-path', filePath),

  // 窗口控制
  windowMinimize: () => ipcRenderer.send('window-minimize'),
  windowMaximize: () => ipcRenderer.send('window-maximize'),
  windowClose: () => ipcRenderer.send('window-close'),

  // 事件监听
  onPublishAction: (callback: (action: string) => void) => {
    ipcRenderer.on('publish-action', (_, action) => callback(action))
    return () => {
      ipcRenderer.removeAllListeners('publish-action')
    }
  },

  // 移除所有监听
  removeAllListeners: (channel: string) => {
    ipcRenderer.removeAllListeners(channel)
  }
}

// 暴露 API
contextBridge.exposeInMainWorld('electronAPI', electronAPI)

// 类型声明
export type ElectronAPI = typeof electronAPI
