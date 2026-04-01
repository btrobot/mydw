# 得物掘金工具

**版本**: 0.1.0
**技术栈**: Electron + React + FastAPI + Playwright

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.10+
- Git

### 安装依赖

```bash
# 安装前端依赖
cd frontend
npm install

# 安装后端依赖
cd ../backend
pip install -r requirements.txt
```

### 开发模式

```bash
# 终端1: 启动后端
cd backend
uvicorn main:app --reload --port 8000

# 终端2: 启动前端
cd frontend
npm run dev
```

### 构建

```bash
# 构建 Electron 应用
npm run build
```

## 项目结构

```
dewugojin/
├── frontend/          # Electron + React 前端
├── backend/           # Python FastAPI 后端
└── README.md
```

## 开发指南

详见 ARCHITECTURE.md
