---
paths:
  - "frontend/electron/**/*.ts"
---

# Electron Security Rules

适用于 `frontend/electron/` 目录下的 Electron 主进程代码。

## Security Configuration

### Main Process

- nodeIntegration MUST be disabled
- contextIsolation MUST be enabled
- sandbox SHOULD be enabled
- webSecurity MUST be enabled

**Correct**:

```typescript
import { BrowserWindow, app } from 'electron'
import path from 'path'

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 600,
    icon: path.join(__dirname, '../public/icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  })
}
```

**Incorrect**:

```typescript
// VIOLATION: insecure configuration
const mainWindow = new BrowserWindow({
  webPreferences: {
    nodeIntegration: true,  // DANGEROUS!
    contextIsolation: false,  // DANGEROUS!
    sandbox: false,
  },
})
```

### Preload Script

- preload script MUST expose minimal API via contextBridge
- MUST NOT expose Node.js APIs directly (fs, child_process, etc.)
- IPC channels SHOULD be validated

**Correct**:

```typescript
// electron/preload.ts
import { contextBridge, ipcRenderer } from 'electron'

// Define allowed channels
const validChannels = [
  'start-backend',
  'stop-backend',
  'get-status',
  'select-folder',
] as const

// Expose minimal, safe API
contextBridge.exposeInMainWorld('electronAPI', {
  startBackend: () => {
    return ipcRenderer.invoke('start-backend')
  },

  stopBackend: () => {
    return ipcRenderer.invoke('stop-backend')
  },

  getStatus: () => {
    return ipcRenderer.invoke('get-status')
  },

  selectFolder: () => {
    return ipcRenderer.invoke('select-folder')
  },
})
```

**Incorrect**:

```typescript
// VIOLATION: exposing dangerous APIs
contextBridge.exposeInMainWorld('api', {
  fs: require('fs'),  // DANGEROUS!
  exec: require('child_process').exec,
  shell: require('electron').shell,
  process: process,
})
```

### IPC Communication

**Correct**:

```typescript
// electron/main.ts

// Validate IPC messages
ipcMain.handle('start-backend', async () => {
  try {
    // Start backend process
    return { success: true }
  } catch (error) {
    return { success: false, error: String(error) }
  }
})

ipcMain.handle('select-folder', async () => {
  const { dialog } = require('electron')
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory'],
  })

  // Validate result
  if (result.canceled || !result.filePaths[0]) {
    return { canceled: true }
  }

  return { canceled: false, path: result.filePaths[0] }
})
```

**Incorrect**:

```typescript
// VIOLATION: executing arbitrary commands
ipcMain.handle('run-command', async (event, command: string) => {
  const { exec } = require('child_process')
  exec(command)  // DANGEROUS: arbitrary command execution!
})
```

---

## Process Management

### Backend Process

- backend process SHOULD be managed in main process
- backend startup SHOULD be async and non-blocking
- backend errors SHOULD be logged

**Correct**:

```typescript
import { spawn, ChildProcess } from 'child_process'

let backendProcess: ChildProcess | null = null

export function startBackend() {
  return new Promise((resolve, reject) => {
    backendProcess = spawn('python', ['-m', 'uvicorn', 'main:app'], {
      cwd: path.join(__dirname, '../backend'),
      stdio: ['pipe', 'pipe', 'pipe'],
    })

    backendProcess.stdout?.on('data', (data) => {
      console.log(`Backend: ${data}`)
    })

    backendProcess.stderr?.on('data', (data) => {
      console.error(`Backend Error: ${data}`)
    })

    backendProcess.on('error', (error) => {
      reject(error)
    })

    backendProcess.on('exit', (code) => {
      console.log(`Backend exited with code ${code}`)
      backendProcess = null
    })

    // Wait for startup
    setTimeout(() => resolve(true), 2000)
  })
}

export function stopBackend() {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
}
```

---

## Window Management

### Window State

- window position and size SHOULD be persisted
- close button behavior SHOULD be configurable

**Correct**:

```typescript
import { BrowserWindow } from 'electron'
import fs from 'fs'

function createWindow() {
  // Load saved window state
  const windowState = loadWindowState()

  const mainWindow = new BrowserWindow({
    width: windowState.width,
    height: windowState.height,
    x: windowState.x,
    y: windowState.y,
    webPreferences: {
      // security settings
    },
  })

  // Save state on close
  mainWindow.on('close', () => {
    saveWindowState({
      width: mainWindow.getBounds().width,
      height: mainWindow.getBounds().height,
      x: mainWindow.getBounds().x,
      y: mainWindow.getBounds().y,
    })
  })
}
```

### Tray (Optional)

**Correct**:

```typescript
import { Tray, Menu, nativeImage } from 'electron'

let tray: Tray | null = null

function createTray() {
  const icon = nativeImage.createFromPath('public/icon.ico')
  tray = new Tray(icon)

  const contextMenu = Menu.buildFromTemplate([
    { label: '显示', click: () => mainWindow?.show() },
    { label: '隐藏', click: () => mainWindow?.hide() },
    { type: 'separator' },
    { label: '退出', click: () => app.quit() },
  ])

  tray.setToolTip('得物掘金工具')
  tray.setContextMenu(contextMenu)

  tray.on('click', () => {
    mainWindow?.show()
  })
}
```

---

## Prohibited Patterns

- MUST NOT enable `nodeIntegration`
- MUST NOT disable `contextIsolation`
- MUST NOT expose `fs`, `child_process`, `process` to renderer
- MUST NOT execute arbitrary user input as commands
- MUST NOT load remote content without validation
- MUST NOT disable `webSecurity` in production

---

## Rationale

These rules prevent:
- Remote code execution through renderer process
- File system access from renderer
- Privilege escalation attacks
- Arbitrary command execution
- Injection attacks through IPC

## Related Rules

- `typescript-coding-rules.md` — Frontend coding standards
- `security-rules.md` — General security requirements
- `python-coding-rules.md` — Backend security patterns
