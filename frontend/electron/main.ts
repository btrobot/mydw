/**
 * 得物掘金工具 - Electron 主进程
 */
import { app, BrowserWindow, Menu, ipcMain, shell, Tray, nativeImage } from 'electron'
import path from 'path'
import { spawn, ChildProcess } from 'child_process'

// 禁用硬件加速
app.disableHardwareAcceleration()

let mainWindow: BrowserWindow | null = null
let tray: Tray | null = null
let backendProcess: ChildProcess | null = null
let isQuitting = false

const isDev = !app.isPackaged

// 开发环境 URL
const VITE_DEV_SERVER_URL = 'http://localhost:5173'

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
              message: '得物掘金工具 v0.1.0',
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
function startBackend() {
  const backendPath = isDev
    ? path.join(__dirname, '../../backend')
    : path.join(__dirname, '../app.asar.unpacked/backend')

  const pythonPath = isDev
    ? path.join(__dirname, '../../backend/venv/Scripts/python.exe')
    : 'python'

  console.log('[Main] 启动后端服务...')

  backendProcess = spawn(pythonPath, ['-m', 'uvicorn', 'main:app', '--port', '8000', '--host', '127.0.0.1'], {
    cwd: path.join(__dirname, '../../backend'),
    stdio: ['pipe', 'pipe', 'pipe'],
    shell: true,
    detached: false
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
app.whenReady().then(() => {
  console.log('[Main] 应用启动...')

  // 设置 IPC 处理器
  setupIpcHandlers()

  // 创建窗口
  createWindow()

  // 创建托盘
  createTray()

  // 启动后端
  startBackend()

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
