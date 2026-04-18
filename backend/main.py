"""
???? - FastAPI ???
"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# ????????????? Python ?
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from loguru import logger

from api import (
    account,
    ai,
    audio,
    auth,
    copywriting,
    cover,
    creative,
    creative_publish_pool,
    creative_review,
    creative_workflows,
    product,
    profile,
    publish,
    schedule_config,
    system,
    task,
    topic,
    video,
)
from api.auth import admin_router as auth_admin_router
from api.topic import group_router as topic_group_router
import models as _models
from core.auth_metrics import PrometheusMetricsExporter, auth_metrics_collector
from models import init_db, PublishProfile
from core.config import settings

# ????
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifecycle hooks."""
    logger.info("?????...")
    auth_metrics_collector.register()
    await init_db()
    logger.info("?????")
    await _seed_default_publish_profile()
    try:
        yield
    finally:
        auth_metrics_collector.unregister()
        logger.info("??????")


# ?? FastAPI ??
app = FastAPI(
    title="??????? API",
    description="?????????????",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ?? CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ????
app.include_router(auth.router, prefix="/api/auth", tags=["??"])
app.include_router(auth_admin_router, prefix="/api", tags=["????"])
app.include_router(account.router, prefix="/api/accounts", tags=["????"])
app.include_router(task.router, prefix="/api/tasks", tags=["????"])
app.include_router(publish.router, prefix="/api/publish", tags=["????"])
app.include_router(schedule_config.router, prefix="/api", tags=["????"])
app.include_router(system.router, prefix="/api/system", tags=["????"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI ??"])
app.include_router(product.router, prefix="/api/products", tags=["????"])
app.include_router(video.router, prefix="/api/videos", tags=["????"])
app.include_router(copywriting.router, prefix="/api/copywritings", tags=["????"])
app.include_router(cover.router, prefix="/api/covers", tags=["????"])
app.include_router(audio.router, prefix="/api/audios", tags=["????"])
app.include_router(topic.router, prefix="/api/topics", tags=["????"])
app.include_router(topic_group_router, prefix="/api/topic-groups", tags=["?????"])
app.include_router(profile.router, prefix="/api/profiles", tags=["????"])
app.include_router(creative.router, prefix="/api/creatives", tags=["????"])
app.include_router(creative_review.router, prefix="/api/creative-reviews", tags=["????"])
app.include_router(creative_publish_pool.router, prefix="/api/creative-publish-pool", tags=["???"])
app.include_router(creative_workflows.router, prefix="/api/creative-workflows", tags=["Creative workflow"])

metrics_exporter = PrometheusMetricsExporter(auth_metrics_collector)


async def _seed_default_publish_profile() -> None:
    """???????????????"""
    async with _models.async_session() as session:
        result = await session.execute(select(PublishProfile))
        if result.scalars().first() is None:
            default_profile = PublishProfile(
                name="????",
                is_default=True,
                composition_mode="none",
            )
            session.add(default_profile)
            await session.commit()
            logger.info("?????????: name=????")


@app.get("/")
async def root():
    """????"""
    return {
        "name": "??????? API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    """?????"""
    return {"status": "healthy"}


@app.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
async def metrics() -> str:
    """Prometheus metrics endpoint."""
    return metrics_exporter.export()


if __name__ == "__main__":
    import uvicorn
    # ????????? reload=True?uvicorn reload ? Windows ????? SelectorEventLoop?
    # ??? Patchright/Playwright ???????????NotImplementedError??
    # ???? watchfiles ?????
    #   watchfiles "venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000" ./
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
