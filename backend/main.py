"""
得物掘金工具 - FastAPI 后端入口
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from loguru import logger

from api import account, task, publish, schedule_config, system, ai, product, video, copywriting, cover, audio, topic, profile
from api.topic import group_router as topic_group_router
import models as _models
from models import init_db, PublishProfile
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
    version=settings.APP_VERSION,
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
app.include_router(publish.router, prefix="/api/publish", tags=["发布控制"])
app.include_router(schedule_config.router, prefix="/api", tags=["调度配置"])
app.include_router(system.router, prefix="/api/system", tags=["系统"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI剪辑"])
app.include_router(product.router, prefix="/api/products", tags=["商品管理"])
app.include_router(video.router, prefix="/api/videos", tags=["视频管理"])
app.include_router(copywriting.router, prefix="/api/copywritings", tags=["文案管理"])
app.include_router(cover.router, prefix="/api/covers", tags=["封面管理"])
app.include_router(audio.router, prefix="/api/audios", tags=["音频管理"])
app.include_router(topic.router, prefix="/api/topics", tags=["话题管理"])
app.include_router(topic_group_router, prefix="/api/topic-groups", tags=["话题组管理"])
app.include_router(profile.router, prefix="/api/profiles", tags=["配置档管理"])


@app.on_event("startup")
async def startup():
    """应用启动事件"""
    logger.info("得物掘金工具后端服务启动中...")
    await init_db()
    logger.info("数据库初始化完成")
    await _seed_default_publish_profile()


async def _seed_default_publish_profile() -> None:
    """系统启动时确保存在默认合成配置档（幂等）。"""
    async with _models.async_session() as session:
        result = await session.execute(select(PublishProfile))
        if result.scalars().first() is None:
            default_profile = PublishProfile(
                name="默认配置",
                is_default=True,
                composition_mode="none",
            )
            session.add(default_profile)
            await session.commit()
            logger.info("已创建默认合成配置档: name=默认配置")


@app.on_event("shutdown")
async def shutdown():
    """应用关闭事件"""
    logger.info("得物掘金工具后端服务关闭")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "得物掘金工具 API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    # 不使用 reload=True，因为 uvicorn reload 在 Windows 上强制使用 SelectorEventLoop，
    # 导致 Patchright/Playwright 无法创建子进程 (NotImplementedError)。
    # 开发时使用 watchfiles 外部热重载:
    #   watchfiles "venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000" ./
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
