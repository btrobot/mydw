/**
 * 得物掘金工具 - Electron 主进程
 */
import { app, BrowserWindow, Menu, ipcMain, shell, Tray, nativeImage, dialog } from 'electron'
import path from 'path'
import { spawn, ChildProcess } from 'child_process'
import { BackendStartupError, createBackendLauncherSpec, waitForBackendHealth } from './backendLauncher'

// 禁用硬件加速
app.disableHardwareAcceleration()

let mainWindow: BrowserWindow | null = null
let tray: Tray | null = null
let backendProcess: ChildProcess | null = null
let isQuitting = false

const isDev = !app.isPackaged

// 开发环境 URL
const VITE_DEV_SERVER_URL = 'http://localhost:5173'
const BACKEND_HEALTH_TIMEOUT_MS = 15000
const BACKEND_HEALTH_RETRY_MS = 500

// 创建主窗口
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    title: '得物掘金工具',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
    show: false,
  })

  // 窗口准备好后显示
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show()
  })

  // 加载页面
  if (isDev) {
    mainWindow.loadURL(VITE_DEV_SERVER_URL)
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  // 窗口关闭时最小化到托盘
  mainWindow.on('close', (event) => {
    if (tray && !isQuitting) {
      event.preventDefault()
      mainWindow?.hide()
    }
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  // 创建菜单
  createMenu()
}

// 创建系统菜单
function createMenu() {
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: '文件',
      submenu: [
        {
          label: '退出',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            isQuitting = true
            app.quit()
          }
        }
      ]
    },
    {
      label: '编辑',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' }
      ]
    },
    {
      label: '视图',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '关于',
          click: () => {
            const { dialog } = require('electron')
            dialog.showMessageBox({
              type: 'info',
              title: '关于得物掘金工具',
              message: `得物掘金工具 v${app.getVersion()}`,
              detail: '得物平台自动化发布系统\n基于 Electron + React + FastAPI'
            })
          }
        }
      ]
    }
  ]

  const menu = Menu.buildFromTemplate(template)
  Menu.setApplicationMenu(menu)
}

// 创建系统托盘
function createTray() {
  // 创建简单的托盘图标
  const iconPath = isDev
    ? path.join(__dirname, '../public/icon.png')
    : path.join(__dirname, '../dist/icon.png')

  try {
    const icon = nativeImage.createFromPath(iconPath)
    tray = new Tray(icon.isEmpty() ? nativeImage.createEmpty() : icon)
  } catch {
    tray = new Tray(nativeImage.createEmpty())
  }

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示窗口',
      click: () => {
        mainWindow?.show()
      }
    },
    {
      label: '开始发布',
      click: () => {
        mainWindow?.webContents.send('publish-action', 'start')
      }
    },
    {
      label: '暂停发布',
      click: () => {
        mainWindow?.webContents.send('publish-action', 'pause')
      }
    },
    { type: 'separator' },
    {
      label: '退出',
      click: () => {
        isQuitting = true
        app.quit()
      }
    }
  ])

  tray.setToolTip('得物掘金工具')
  tray.setContextMenu(contextMenu)

  tray.on('double-click', () => {
    mainWindow?.show()
  })
}

// 启动后端服务
async function startBackend() {
  const launcher = createBackendLauncherSpec({
    isDev,
    electronDir: __dirname,
    resourcesPath: process.resourcesPath,
  })

  console.log('[Main] 启动后端服务...', {
    backendPath: launcher.backendPath,
    command: launcher.command,
    args: launcher.args,
    healthUrl: launcher.healthUrl,
    isDev,
  })

  backendProcess = spawn(launcher.command, launcher.args, {
    cwd: launcher.cwd,
    env: launcher.env,
    stdio: ['pipe', 'pipe', 'pipe'],
    detached: false,
    shell: false,
  })

  backendProcess.stdout?.on('data', (data) => {
    console.log('[Backend]', data.toString())
  })

  backendProcess.stderr?.on('data', (data) => {
    console.error('[Backend Error]', data.toString())
  })

  backendProcess.on('error', (err) => {
    console.error('[Backend Error]', err)
  })

  backendProcess.on('exit', (code) => {
    console.log('[Backend] 进程退出, code:', code)
  })

  await waitForBackendHealth(backendProcess, launcher.healthUrl, {
    timeoutMs: BACKEND_HEALTH_TIMEOUT_MS,
    retryIntervalMs: BACKEND_HEALTH_RETRY_MS,
  })
}

// 停止后端服务
function stopBackend() {
  if (backendProcess) {
    console.log('[Main] 停止后端服务...')
    backendProcess.kill()
    backendProcess = null
  }
}

// IPC 处理器
function setupIpcHandlers() {
  // 获取版本
  ipcMain.handle('get-version', () => {
    return app.getVersion()
  })

  // 获取平台
  ipcMain.handle('get-platform', () => {
    return process.platform
  })

  // 打开外部链接
  ipcMain.handle('open-external', async (_, url: string) => {
    await shell.openExternal(url)
  })

  // 打开文件夹
  ipcMain.handle('open-path', async (_, filePath: string) => {
    shell.showItemInFolder(filePath)
  })

  // 窗口控制
  ipcMain.on('window-minimize', () => {
    mainWindow?.minimize()
  })

  ipcMain.on('window-maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow?.maximize()
    }
  })

  ipcMain.on('window-close', () => {
    mainWindow?.close()
  })
}

// 应用就绪
app.whenReady().then(async () => {
  console.log('[Main] 应用启动...')

  // 设置 IPC 处理器
  setupIpcHandlers()

  try {
    // 先启动并等待后端健康，再创建窗口/托盘
    await startBackend()
  } catch (error) {
    const message = error instanceof BackendStartupError
      ? `[${error.code}] ${error.message}`
      : error instanceof Error
        ? error.message
        : '未知错误'

    console.error('[Main] 后端启动失败:', message)
    stopBackend()
    dialog.showErrorBox('后端启动失败', message)
    app.quit()
    return
  }

  // 创建窗口
  createWindow()

  // 创建托盘
  createTray()

  // macOS 激活时重新创建窗口
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

// 所有窗口关闭
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// 退出前清理
app.on('before-quit', () => {
  console.log('[Main] 应用退出...')
  stopBackend()
})

app.on('quit', () => {
  console.log('[Main] 应用已退出')
})
