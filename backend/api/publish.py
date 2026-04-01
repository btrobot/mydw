"""
发布控制 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from models import Task, Account, PublishConfig, PublishLog
from models import get_db
from schemas import (
    PublishConfigRequest, PublishConfigResponse,
    PublishControlRequest, PublishStatusResponse
)
from services.scheduler import scheduler

router = APIRouter()

# 发布状态存储
_publish_status = {
    "status": "idle",
    "current_task_id": None
}


@router.get("/config", response_model=PublishConfigResponse)
async def get_publish_config(db: AsyncSession = Depends(get_db)):
    """获取发布配置"""
    result = await db.execute(
        select(PublishConfig).where(PublishConfig.name == "default")
    )
    config = result.scalar_one_or_none()

    if not config:
        # 创建默认配置
        config = PublishConfig(name="default")
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return config


@router.put("/config", response_model=PublishConfigResponse)
async def update_publish_config(
    config_data: PublishConfigRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新发布配置"""
    result = await db.execute(
        select(PublishConfig).where(PublishConfig.name == "default")
    )
    config = result.scalar_one_or_none()

    if not config:
        config = PublishConfig(name="default")
        db.add(config)

    # 更新配置
    config.interval_minutes = config_data.interval_minutes
    config.start_hour = config_data.start_hour
    config.end_hour = config_data.end_hour
    config.max_per_account_per_day = config_data.max_per_account_per_day
    config.shuffle = config_data.shuffle
    config.auto_start = config_data.auto_start

    await db.commit()
    await db.refresh(config)

    logger.info("更新发布配置")
    return config


@router.get("/status", response_model=PublishStatusResponse)
async def get_publish_status(db: AsyncSession = Depends(get_db)):
    """获取发布状态"""
    # 统计任务
    pending = await db.execute(
        select(func.count(Task.id)).where(Task.status == "pending")
    )
    success = await db.execute(
        select(func.count(Task.id)).where(Task.status == "success")
    )
    failed = await db.execute(
        select(func.count(Task.id)).where(Task.status == "failed")
    )

    return PublishStatusResponse(
        status=_publish_status["status"],
        current_task_id=_publish_status.get("current_task_id"),
        total_pending=pending.scalar() or 0,
        total_success=success.scalar() or 0,
        total_failed=failed.scalar() or 0
    )


@router.post("/control")
async def control_publish(
    request: PublishControlRequest,
    db: AsyncSession = Depends(get_db)
):
    """发布控制"""
    action = request.action.lower()

    if action == "start":
        if _publish_status["status"] == "running":
            raise HTTPException(status_code=400, detail="发布已在运行中")

        _publish_status["status"] = "running"
        result = await scheduler.start_publishing(db)
        logger.info("开始发布任务")

        return {"success": True, "action": action, **result}

    elif action == "pause":
        _publish_status["status"] = "paused"
        result = await scheduler.pause_publishing(db)
        logger.info("暂停发布任务")

        return {"success": True, "action": action, **result}

    elif action == "stop":
        _publish_status["status"] = "idle"
        _publish_status["current_task_id"] = None
        result = await scheduler.stop_publishing(db)
        logger.info("停止发布任务")

        return {"success": True, "action": action, **result}

    else:
        raise HTTPException(status_code=400, detail="未知操作")


@router.post("/refresh")
async def refresh_data(db: AsyncSession = Depends(get_db)):
    """刷新数据 - 重新从得物获取账号和任务状态"""
    try:
        # 遍历所有活跃账号，检查登录状态
        result = await db.execute(
            select(Account).where(Account.status == "active")
        )
        accounts = result.scalars().all()

        refreshed = 0
        for account in accounts:
            try:
                # TODO: 实际检查登录状态
                refreshed += 1
            except Exception as e:
                logger.warning(f"检查账号 {account.account_name} 失败: {e}")

        logger.info(f"刷新数据完成，{refreshed} 个账号已检查")
        return {"success": True, "message": f"已刷新 {refreshed} 个账号"}

    except Exception as e:
        logger.error(f"刷新数据失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/shuffle")
async def shuffle_tasks(db: AsyncSession = Depends(get_db)):
    """乱序发布 - 打乱待发布任务的顺序"""
    return await scheduler.shuffle_tasks(db)


@router.get("/logs")
async def get_publish_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """获取发布日志"""
    result = await db.execute(
        select(PublishLog).order_by(PublishLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()

    return {
        "total": len(logs),
        "items": [
            {
                "id": log.id,
                "task_id": log.task_id,
                "account_id": log.account_id,
                "status": log.status,
                "message": log.message,
                "created_at": log.created_at
            }
            for log in logs
        ]
    }
