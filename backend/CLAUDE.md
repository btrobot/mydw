> Updated: 2026-04-07

# Backend 开发规范

## 虚拟环境

Python 虚拟环境位于 `backend/venv/`。

### 激活方式

**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
.\venv\Scripts\activate.bat
```

### 运行命令

使用虚拟环境中的 Python：

```powershell
# 启动服务
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

# 运行脚本
.\venv\Scripts\python.exe script.py

# 安装依赖
.\venv\Scripts\pip.exe install package-name
```

## 项目结构

```
backend/
├── api/              # API 路由
│   ├── account.py    # 账号管理
│   ├── task.py       # 任务管理
│   ├── material.py   # 素材管理
│   ├── publish.py    # 发布控制
│   ├── system.py     # 系统
│   └── ai.py         # AI 剪辑
├── core/             # 核心模块
│   ├── browser.py    # Playwright 浏览器管理
│   ├── dewu_client.py # 得物客户端
│   └── config.py     # 配置
├── models/           # SQLAlchemy 模型
├── schemas/          # Pydantic Schema
├── services/         # 业务服务
├── utils/            # 工具函数
│   └── crypto.py     # 加密工具
├── logs/             # 日志目录
├── main.py           # FastAPI 入口
└── venv/             # 虚拟环境 ⭐
```

## 依赖管理

### PyPI 镜像

**开发期间使用清华镜像加速：**
```powershell
# 设置全局镜像
.\venv\Scripts\pip.exe config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 或安装时指定
.\venv\Scripts\pip.exe install -i https://pypi.tuna.tsinghua.edu.cn/simple package-name
```

### 常用命令

```powershell
# 导出当前依赖
.\venv\Scripts\pip.exe freeze > requirements.txt

# 从 requirements 安装（使用镜像）
.\venv\Scripts\pip.exe install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装单个包（使用镜像）
.\venv\Scripts\pip.exe install scrapling -i https://pypi.tuna.tsinghua.edu.cn/simple

# 升级包
.\venv\Scripts\pip.exe install --upgrade package-name -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 数据库

- 类型: SQLite (aiosqlite)
- 路径: `backend/data/dewugojin.db`
- 初始化: 启动时自动创建

## Playwright

```powershell
# 安装浏览器
.\venv\Scripts\playwright.exe install chromium

# 安装依赖
.\venv\Scripts\playwright.exe install-deps
```
