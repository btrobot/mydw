
● 前端技术栈

  ┌─────────────────────────────────────────────────────────────┐
  │                      技术栈总览                              │                                                                   ├─────────────────────────────────────────────────────────────┤
  │  桌面框架    │  Electron 28                                  │                                                                   │  UI 框架     │  React 18 + TypeScript 5                     │
  │  构建工具    │  Vite 5                                       │
  │  组件库      │  Ant Design 5                                │
  │  状态管理    │  Zustand 4                                   │
  │  HTTP 客户端 │  Axios                                       │
  │  路由        │  React Router 6                              │
  │  图标        │  @ant-design/icons                           │
  │  日期处理    │  Dayjs                                       │
  └─────────────────────────────────────────────────────────────┘

  ---
  1. 桌面框架: Electron 28

  特点:
  - 跨平台桌面应用 (Windows/macOS/Linux)
  - 原生系统集成 (托盘、通知、系统菜单)
  - Node.js 后端集成

  // frontend/electron/main.ts
  import { app, BrowserWindow, Tray, Menu } from 'electron'

  // 创建主窗口
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 600,
    webPreferences: { nodeIntegration: false },
    icon: 'public/icon.ico'
  })

  // 系统托盘
  const tray = new Tray('public/icon.ico')
  tray.setContextMenu(Menu.buildFromTemplate([...]))

  ---
  2. UI 框架: React 18 + TypeScript 5

  为什么选择:
  - 函数式组件 + Hooks
  - 严格类型检查
  - 生态系统丰富

  // frontend/src/pages/AIClip.tsx
  interface VideoInfo {
    path: string
    duration: number
    width: number
    height: number
    fps: number
  }

  export default function AIClip() {
    const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null)
    // ...
  }

  TypeScript 配置 (tsconfig.json):

  {
    "compilerOptions": {
      "target": "ES2020",
      "strict": true,           // 严格模式
      "noUnusedLocals": true,   // 检查未使用变量
      "noUnusedParameters": true
    }
  }

  ---
  3. 构建工具: Vite 5

  优势:
  - 极速开发服务器启动
  - 热模块替换 (HMR)
  - 优化的生产构建

  // vite.config.ts
  export default defineConfig({
    plugins: [react()],
    server: { port: 5173 },
    build: { outDir: 'dist' }
  })

  ---
  4. 组件库: Ant Design 5

  特点:
  - 企业级 UI 组件
  - 中文本地化支持
  - 主题定制

  // frontend/src/App.tsx
  import { ConfigProvider } from 'antd'
  import zhCN from 'antd/locale/zh_CN'

  const theme = {
    token: { colorPrimary: '#1890ff', borderRadius: 6 }
  }

  function App() {
    return (
      <ConfigProvider theme={theme} locale={zhCN}>
        {/* ... */}
      </ConfigProvider>
    )
  }

  常用组件:

  ┌──────────────────┬────────────┐
  │       组件       │    用途    │
  ├──────────────────┼────────────┤
  │ Table            │ 数据列表   │
  ├──────────────────┼────────────┤
  │ Form + Form.Item │ 表单输入   │
  ├──────────────────┼────────────┤
  │ Modal            │ 弹窗对话框 │
  ├──────────────────┼────────────┤
  │ Button           │ 按钮操作   │
  ├──────────────────┼────────────┤
  │ Card             │ 卡片布局   │
  ├──────────────────┼────────────┤
  │ Row + Col        │ 栅格布局   │
  ├──────────────────┼────────────┤
  │ message          │ 消息提示   │
  ├──────────────────┼────────────┤
  │ Tag              │ 状态标签   │
  └──────────────────┴────────────┘

  ---
  5. 状态管理: Zustand 4

  优势:
  - 极简 API
  - 轻量级 (~1kb)
  - TypeScript 友好

  // frontend/src/stores/accountStore.ts
  import { create } from 'zustand'

  interface AccountState {
    accounts: Account[]
    loading: boolean
    fetchAccounts: () => Promise<void>
  }

  export const useAccountStore = create<AccountState>((set) => ({
    accounts: [],
    loading: false,
    fetchAccounts: async () => {
      set({ loading: true })
      const res = await api.get('/accounts')
      set({ accounts: res.data, loading: false })
    }
  }))

  // 使用
  const { accounts, fetchAccounts } = useAccountStore()

  ---
  6. HTTP 客户端: Axios

  // frontend/src/services/api.ts
  import axios from 'axios'

  export const api = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
    timeout: 30000,
  })

  // 请求拦截器
  api.interceptors.request.use((config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  })

  // 响应拦截器
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      console.error('[API Error]', error.response?.data)
      return Promise.reject(error)
    }
  )

  ---
  7. 路由: React Router 6

  // frontend/src/App.tsx
  import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
  import Layout from './components/Layout'

  function App() {
    return (
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="account" element={<Account />} />
            <Route path="task" element={<Task />} />
            <Route path="ai-clip" element={<AIClip />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    )
  }

  ---
  项目结构

  frontend/
  ├── electron/               # Electron 主进程
  │   └── main.ts            # 主进程入口
  ├── public/                 # 静态资源
  │   └── icon.ico           # 应用图标
  ├── src/
  │   ├── main.tsx           # React 入口
  │   ├── App.tsx            # 根组件
  │   ├── components/        # 公共组件
  │   │   └── Layout.tsx     # 页面布局
  │   ├── pages/             # 页面组件
  │   │   ├── Dashboard.tsx  # 数据看板
  │   │   ├── Account.tsx    # 账号管理
  │   │   ├── Task.tsx       # 任务管理
  │   │   ├── Material.tsx   # 素材管理
  │   │   ├── AIClip.tsx     # AI 剪辑
  │   │   └── Settings.tsx  # 系统设置
  │   ├── services/         # API 服务
  │   │   └── api.ts         # Axios 封装
  │   ├── stores/            # Zustand 状态
  │   └── types/             # 类型定义
  ├── index.html             # HTML 入口
  ├── package.json
  ├── tsconfig.json
  └── vite.config.ts

  ---
  页面展示

  ┌──────────────────────────────────────────────────────────┐
  │  得物掘金工具                                              │
  ├────────────┬─────────────────────────────────────────────┤
  │            │                                             │
  │  Dashboard │                                             │
  │  账号管理   │              页面内容区域                     │
  │  任务管理   │                                             │
  │  素材管理   │                                             │
  │  AI 剪辑   │                                             │
  │  系统设置   │                                             │
  │            │                                             │
  ├────────────┴─────────────────────────────────────────────┤
  │  状态栏                                                  │
  └──────────────────────────────────────────────────────────┘

  ---
  启动方式

  cd frontend
  npm install

  # Web 开发模式
  npm run dev              # http://localhost:5173

  # Electron 开发模式
  npm run dev:electron     # 同时启动前端 + Electron

  # 构建桌面应用
  npm run build:electron   # 输出到 frontend/release/

✻ Brewed for 59s

─
