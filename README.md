# 得物掘金工具

**版本**: 0.2.0
**技术栈**: Electron + React + Vite + FastAPI + Playwright + FFmpeg

得物平台自动化视频发布系统，支持多账号管理、智能素材剪辑、任务定时发布。

## 功能特性

- **账号管理**: 多账号 cookie 加密存储，浏览器上下文隔离
- **素材管理**: 视频、文案、封面、话题、音频素材分类管理
- **AI 剪辑**: 基于 FFmpeg 的智能视频剪辑，高光检测，背景音乐添加
- **任务发布**: 可视化任务配置，定时发布，发布日志记录
- **Electron 桌面**: 原生窗口控制，系统托盘，后台运行

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.10+
- FFmpeg (用于 AI 剪辑功能)
- Git

### 安装依赖

```bash
# 使用启动脚本（推荐）
.\dev.bat

# 或手动安装

# 前端依赖
cd frontend
npm install

# 后端依赖
cd ../backend
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
python -m playwright install chromium
```

### 启动服务

```bash
# Windows
.\dev.bat

# 或手动启动
# 终端1: 后端
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000

# 终端2: 前端
cd frontend
npm run dev
```

### 访问地址

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 项目结构

```
dewugojin/
├── frontend/                    # Electron + React 前端
│   ├── src/
│   │   ├── pages/               # 页面组件
│   │   │   ├── Dashboard.tsx    # 数据看板
│   │   │   ├── Account.tsx      # 账号管理
│   │   │   ├── Task.tsx         # 任务管理
│   │   │   ├── Material.tsx     # 素材管理
│   │   │   ├── AIClip.tsx       # AI 智能剪辑
│   │   │   └── Settings.tsx     # 系统设置
│   │   ├── components/          # 公共组件
│   │   └── services/            # API 服务
│   └── electron/                # Electron 配置
├── backend/                      # Python FastAPI 后端
│   ├── api/                     # API 路由
│   │   ├── account.py           # 账号管理
│   │   ├── task.py              # 任务管理
│   │   ├── material.py          # 素材管理
│   │   ├── publish.py           # 发布控制
│   │   ├── ai.py                # AI 剪辑
│   │   └── system.py            # 系统接口
│   ├── models/                  # 数据库模型
│   ├── services/                # 业务服务
│   │   ├── browser_service.py  # 浏览器自动化
│   │   └── ai_clip_service.py  # AI 剪辑服务
│   └── core/                    # 核心配置
├── data/                        # 素材存储目录
│   ├── video/                   # 视频素材
│   ├── audio/                   # 音频素材
│   ├── cover/                   # 封面素材
│   ├── text/                    # 文案素材
│   └── topic/                   # 话题素材
└── README.md
```

## API 接口

### 账号管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/accounts | 获取账号列表 |
| POST | /api/accounts | 创建账号 |
| PUT | /api/accounts/{id} | 更新账号 |
| DELETE | /api/accounts/{id} | 删除账号 |
| POST | /api/accounts/{id}/login | 登录账号 |
| POST | /api/accounts/{id}/logout | 登出账号 |

### 素材管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/materials | 获取素材列表 |
| POST | /api/materials/upload/{type} | 上传素材 |
| GET | /api/materials/stats | 获取统计 |
| POST | /api/materials/scan | 扫描本地素材 |
| POST | /api/materials/import | 批量导入素材 |

### AI 剪辑

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/ai/video-info | 获取视频信息 |
| GET | /api/ai/detect-highlights | 检测高光片段 |
| POST | /api/ai/smart-clip | 智能剪辑 |
| POST | /api/ai/add-audio | 添加背景音乐 |
| POST | /api/ai/add-cover | 添加封面 |
| POST | /api/ai/full-pipeline | 完整剪辑流程 |

### 任务管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/tasks | 获取任务列表 |
| POST | /api/tasks | 创建任务 |
| PUT | /api/tasks/{id} | 更新任务 |
| DELETE | /api/tasks/{id} | 删除任务 |
| POST | /api/tasks/{id}/execute | 执行任务 |
| POST | /api/tasks/batch-execute | 批量执行 |

## 数据安全

- Cookie 使用 AES-256-GCM 加密存储
- 密钥由环境变量 `SECRET_KEY` 配置
- 数据库文件位于 `backend/data/dewugojin.db`

## 构建应用

```bash
cd frontend
npm run build
```

打包后的应用位于 `frontend/release/` 目录。

## 开发指南

详见 [ARCHITECTURE.md](ARCHITECTURE.md)
