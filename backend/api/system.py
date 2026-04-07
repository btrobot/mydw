"""
系统 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List
from datetime import datetime
from pathlib import Path
from loguru import logger

from models import Account, Task, Product, SystemLog, PublishConfig, Video, Copywriting, Cover, Audio, Topic
from models import get_db
from schemas import (
    SystemStats, SystemLogResponse, SystemLogListResponse,
    BackupRequest,
)

router = APIRouter()


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    """获取系统统计"""
    # 账号统计
    total_accounts = await db.execute(select(func.count(Account.id)))
    active_accounts = await db.execute(
        select(func.count(Account.id)).where(Account.status == "active")
    )

    # 任务统计
    total_tasks = await db.execute(select(func.count(Task.id)))
    pending_tasks = await db.execute(
        select(func.count(Task.id)).where(Task.status == "pending")
    )
    success_tasks = await db.execute(
        select(func.count(Task.id)).where(Task.status == "success")
    )
    failed_tasks = await db.execute(
        select(func.count(Task.id)).where(Task.status == "failed")
    )

    # 商品统计
    total_products = await db.execute(select(func.count(Product.id)))

    return SystemStats(
        total_accounts=total_accounts.scalar() or 0,
        active_accounts=active_accounts.scalar() or 0,
        total_tasks=total_tasks.scalar() or 0,
        pending_tasks=pending_tasks.scalar() or 0,
        success_tasks=success_tasks.scalar() or 0,
        failed_tasks=failed_tasks.scalar() or 0,
        total_products=total_products.scalar() or 0
    )


@router.get("/logs", response_model=SystemLogListResponse)
async def get_system_logs(
    level: str = None,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """获取系统日志"""
    query = select(SystemLog)

    if level:
        query = query.where(SystemLog.level == level.upper())

    query = query.order_by(desc(SystemLog.created_at)).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return SystemLogListResponse(total=len(logs), items=logs)


@router.post("/logs")
async def add_system_log(
    level: str,
    message: str,
    module: str = None,
    details: str = None,
    db: AsyncSession = Depends(get_db)
):
    """添加系统日志"""
    log = SystemLog(
        level=level.upper(),
        module=module,
        message=message,
        details=details
    )
    db.add(log)
    await db.commit()

    return {"success": True}


@router.get("/config")
async def get_system_config(db: AsyncSession = Depends(get_db)):
    """获取系统配置"""
    # TODO: 从配置文件读取
    return {
        "material_base_path": "D:/系统/桌面/得物剪辑/待上传数据",
        "auto_backup": False,
        "log_level": "INFO"
    }


@router.put("/config")
async def update_system_config(
    material_base_path: str = None,
    auto_backup: bool = None,
    log_level: str = None
):
    """更新系统配置"""
    # TODO: 保存到配置文件
    logger.info(f"更新系统配置: material_path={material_base_path}")

    return {"success": True}


@router.post("/backup")
async def backup_data(request: BackupRequest, db: AsyncSession = Depends(get_db)):
    """备份数据"""
    backup_dir = Path("data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_{timestamp}.json"

    # TODO: 导出数据库到 JSON
    backup_data = {
        "version": "0.1.0",
        "timestamp": timestamp,
        "accounts": [],
        "tasks": [],
        "materials": [],
        "products": []
    }

    logger.info(f"数据备份: {backup_file}")

    return {
        "success": True,
        "backup_file": str(backup_file)
    }


# ─── SP8-05: 素材统计 ────────────────────────────────────────────────────────

@router.get("/material-stats")
async def material_stats(db: AsyncSession = Depends(get_db)):
    """素材统计：各类数量、商品覆盖率"""
    video_count = (await db.execute(select(func.count()).select_from(Video))).scalar() or 0
    copywriting_count = (await db.execute(select(func.count()).select_from(Copywriting))).scalar() or 0
    cover_count = (await db.execute(select(func.count()).select_from(Cover))).scalar() or 0
    audio_count = (await db.execute(select(func.count()).select_from(Audio))).scalar() or 0
    topic_count = (await db.execute(select(func.count()).select_from(Topic))).scalar() or 0
    product_count = (await db.execute(select(func.count()).select_from(Product))).scalar() or 0

    products_with_video = (await db.execute(
        select(func.count(func.distinct(Video.product_id))).where(Video.product_id.isnot(None))
    )).scalar() or 0

    return {
        "videos": video_count,
        "copywritings": copywriting_count,
        "covers": cover_count,
        "audios": audio_count,
        "topics": topic_count,
        "products": product_count,
        "products_with_video": products_with_video,
        "coverage_rate": round(products_with_video / product_count, 2) if product_count else 0,
    }
