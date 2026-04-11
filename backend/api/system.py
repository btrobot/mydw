"""
系统 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from models import Account, Task, Product, SystemLog, Video, Copywriting, Cover, Audio, Topic
from models import get_db
from schemas import (
    SystemStats, SystemLogListResponse,
    BackupRequest, BackupResponse, MaterialStatsResponse,
    SystemConfigResponse, SystemConfigUpdateResponse,
)
from services.system_backup_service import SystemBackupService
from services.system_config_service import SystemConfigService

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
        select(func.count(Task.id)).where(Task.status == "ready")
    )
    success_tasks = await db.execute(
        select(func.count(Task.id)).where(Task.status == "uploaded")
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


@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config():
    """获取系统设置真相：runtime-config + 只读启动期信息。"""
    return SystemConfigService().get_config()


@router.put("/config", response_model=SystemConfigUpdateResponse)
async def update_system_config(
    material_base_path: str = Query(
        default=None,
        description="当前唯一支持运行时修改的设置项；写入 data/system_config.json。",
    ),
    auto_backup: bool = Query(
        default=None,
        description="兼容占位参数；当前不支持运行时修改，传入时会返回 400。",
    ),
    log_level: str = Query(
        default=None,
        description="只读启动期配置；权威来源是 .env / backend/core/config.py，传入时会返回 400。",
    ),
):
    """更新受支持的 runtime-config；不接受伪配置字段静默成功。"""
    try:
        updated = SystemConfigService().update_config(
            material_base_path=material_base_path,
            auto_backup=auto_backup,
            log_level=log_level,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info("更新系统配置: material_path={}", updated["material_base_path"])

    return SystemConfigUpdateResponse(
        success=True,
        material_base_path=updated["material_base_path"],
        auto_backup=updated["auto_backup"],
        log_level=updated["log_level"],
    )


@router.post("/backup", response_model=BackupResponse)
async def backup_data(request: BackupRequest, db: AsyncSession = Depends(get_db)):
    """备份数据"""
    backup_file = await SystemBackupService(db).create_backup(include_logs=request.include_logs)
    logger.info("数据备份: {}", backup_file)
    return BackupResponse(success=True, backup_file=str(backup_file))


# ─── SP8-05: 素材统计 ────────────────────────────────────────────────────────

@router.get("/material-stats", response_model=MaterialStatsResponse)
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
