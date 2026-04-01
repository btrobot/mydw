"""
得物掘金工具 - FastAPI 后端入口
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api import account, task, material, publish, system, ai
from models import init_db
from core.config import settings

# 配置日志
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
)

# 创建 FastAPI 应用
app = FastAPI(
    title="得物掘金工具 API",
    description="得物平台自动化发布系统后端服务",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(account.router, prefix="/api/accounts", tags=["账号管理"])
app.include_router(task.router, prefix="/api/tasks", tags=["任务管理"])
app.include_router(material.router, prefix="/api/materials", tags=["素材管理"])
app.include_router(publish.router, prefix="/api/publish", tags=["发布控制"])
app.include_router(system.router, prefix="/api/system", tags=["系统"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI剪辑"])


@app.on_event("startup")
async def startup():
    """应用启动事件"""
    logger.info("得物掘金工具后端服务启动中...")
    await init_db()
    logger.info("数据库初始化完成")


@app.on_event("shutdown")
async def shutdown():
    """应用关闭事件"""
    logger.info("得物掘金工具后端服务关闭")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "得物掘金工具 API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
