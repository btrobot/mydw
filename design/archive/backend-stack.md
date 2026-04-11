
  后端技术栈                                                                                                                       
  ┌─────────────────────────────────────────────────────────────┐                                                                    │                      技术栈总览                              │
  ├─────────────────────────────────────────────────────────────┤
  │  Web 框架      │  FastAPI 0.109 + Uvicorn                   │
  │  数据库        │  SQLite + SQLAlchemy (异步)                 │
  │  浏览器自动化  │  Playwright (Chromium)                       │
  │  视频处理     │  FFmpeg + ffprobe                           │
  │  日志         │  Loguru                                      │
  │  验证         │  Pydantic + pydantic-settings                │
  │  HTTP 客户端  │  httpx (异步)                                │
  └─────────────────────────────────────────────────────────────┘

  ---
  1. Web 框架: FastAPI

  为什么选择 FastAPI:
  - 异步支持 - 高并发处理
  - 自动 OpenAPI 文档
  - Pydantic 集成 - 数据验证

  # backend/main.py
  from fastapi import FastAPI
  app = FastAPI(title="得物掘金工具 API")

  # 自动生成 API 文档: http://localhost:8000/docs

  ---
  2. 数据库: SQLAlchemy + aiosqlite

  特点:
  - 异步 ORM - 非阻塞数据库操作
  - SQLite - 轻量级，无需额外服务
  - 关系模型 - Account, Task, Material 等

  # backend/models/__init__.py
  from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

  engine = create_async_engine("sqlite+aiosqlite:///./data/dewugojin.db")
  async_session = sessionmaker(engine, class_=AsyncSession)

  数据模型:

  ┌────────────────┬────────────────────────────┐
  │      表名      │            说明            │
  ├────────────────┼────────────────────────────┤
  │ accounts       │ 账号管理 (Cookie 加密存储) │
  ├────────────────┼────────────────────────────┤
  │ tasks          │ 发布任务                   │
  ├────────────────┼────────────────────────────┤
  │ materials      │ 素材管理                   │
  ├────────────────┼────────────────────────────┤
  │ products       │ 商品信息                   │
  ├────────────────┼────────────────────────────┤
  │ publish_logs   │ 发布日志                   │
  ├────────────────┼────────────────────────────┤
  │ publish_config │ 发布配置                   │
  ├────────────────┼────────────────────────────┤
  │ system_logs    │ 系统日志                   │
  └────────────────┴────────────────────────────┘

  ---
  3. 浏览器自动化: Playwright

  用途:
  - 账号登录 (二维码扫描)
  - 验证 Cookie 有效性
  - 获取登录状态

  # backend/core/browser.py
  from playwright.async_api import async_playwright

  async with async_playwright() as p:
      browser = await p.chromium.launch(headless=True)
      context = await browser.new_context()
      # 自动化操作...

  ---
  4. 视频处理: FFmpeg

  功能:
  - 获取视频信息 (时长/分辨率/帧率)
  - 智能剪辑 - 高光片段提取
  - 添加背景音乐
  - 添加封面

  # backend/services/ai_clip_service.py
  cmd = ["ffmpeg", "-i", video_path, "-ss", start, "-t", duration, output]
  result = await asyncio.create_subprocess_exec(*cmd)

  ---
  5. 日志: Loguru

  优势:
  - 零配置
  - 自动彩色输出
  - 异步支持

  from loguru import logger

  logger.info("任务创建成功: task_id={}", task_id)
  logger.error("处理失败: {}", error, exc_info=True)

  ---
  6. 数据验证: Pydantic

  # backend/schemas/account.py
  from pydantic import BaseModel, Field

  class AccountCreate(BaseModel):
      account_id: str = Field(..., min_length=1)
      account_name: str = Field(..., min_length=1)

      @validator("account_id")
      def validate_account_id(cls, v):
          if len(v) < 5:
              raise ValueError("账号ID长度不足")
          return v

  ---
  项目结构

  backend/
  ├── api/                    # API 路由
  │   ├── __init__.py
  │   ├── account.py          # 账号管理
  │   ├── task.py             # 任务管理
  │   ├── material.py         # 素材管理
  │   ├── publish.py          # 发布控制
  │   ├── ai.py               # AI 剪辑
  │   └── system.py           # 系统接口
  ├── core/                   # 核心模块
  │   ├── config.py           # 配置管理
  │   ├── browser.py          # Playwright 封装
  │   └── dewu_client.py      # 得物客户端
  ├── models/                 # 数据库模型
  │   └── __init__.py
  ├── schemas/                # Pydantic 模型
  │   └── __init__.py
  ├── services/               # 业务服务
  │   ├── ai_clip_service.py  # 视频处理
  │   ├── task_service.py     # 任务服务
  │   ├── material_service.py  # 素材服务
  │   └── scheduler.py        # 定时任务
  ├── utils/                  # 工具函数
  │   └── crypto.py           # 加密工具
  ├── main.py                 # 应用入口
  └── requirements.txt        # 依赖

  ---
  依赖清单

  # backend/requirements.txt
  fastapi>=0.109.0
  uvicorn[standard]>=0.27.0
  sqlalchemy>=2.0.0
  aiosqlite>=0.19.0
  pydantic>=2.5.0
  pydantic-settings>=2.1.0
  playwright>=1.40.0
  httpx>=0.26.0
  loguru>=0.7.0
  python-multipart>=0.0.6

  ---
  启动方式

  cd backend
  pip install -r requirements.txt
  python -m playwright install chromium  # 安装浏览器

  # 开发模式
  uvicorn main:app --reload --port 8000

  # 生产模式
  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

✻
