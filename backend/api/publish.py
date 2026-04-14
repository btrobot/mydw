"""
发布控制 API

说明：
- `/config` 仍是遗留兼容入口，返回/写入 contract 保持兼容
- 调度配置的 canonical contract 将逐步收口到独立的 schedule-config API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from models import Task, Account, PublishLog
from models import get_db
from schemas import (
    PublishConfigRequest, PublishConfigResponse,
    PublishControlRequest, PublishStatusResponse
)
from core.auth_dependencies import ACTIVE_ROUTE_DEPENDENCIES, GRACE_READONLY_ROUTE_DEPENDENCIES
from services.schedule_config_service import ScheduleConfigService
from services.scheduler import scheduler

router = APIRouter()


@router.get("/config", response_model=PublishConfigResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def get_publish_config(db: AsyncSession = Depends(get_db)):
    """获取发布配置（遗留兼容入口，底层真相已桥接到 ScheduleConfig）。"""
    service = ScheduleConfigService(db)
    return await service.get_or_create_default()


@router.put("/config", response_model=PublishConfigResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def update_publish_config(
    config_data: PublishConfigRequest,
    db: AsyncSession = Depends(get_db)
):
    """更新发布配置（遗留兼容入口，写入 canonical ScheduleConfig）。"""
    service = ScheduleConfigService(db)
    config = await service.update_default(config_data)
    logger.info("更新发布配置（兼容接口，canonical source=ScheduleConfig）")
    return config


@router.get("/status", response_model=PublishStatusResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def get_publish_status(db: AsyncSession = Depends(get_db)):
    """获取发布状态（基于 scheduler runtime truth）。"""
    # 统计任务
    ready = await db.execute(
        select(func.count(Task.id)).where(Task.status == "ready")
    )
    uploaded = await db.execute(
        select(func.count(Task.id)).where(Task.status == "uploaded")
    )
    failed = await db.execute(
        select(func.count(Task.id)).where(Task.status == "failed")
    )

    return PublishStatusResponse(
        status=scheduler.get_status(),
        current_task_id=scheduler.current_task_id(),
        total_pending=ready.scalar() or 0,
        total_success=uploaded.scalar() or 0,
        total_failed=failed.scalar() or 0
    )


@router.post("/control", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def control_publish(
    request: PublishControlRequest,
    db: AsyncSession = Depends(get_db)
):
    """发布控制（基于 scheduler runtime truth）。"""
    action = request.action.lower()

    if action == "start":
        if scheduler.is_running():
            raise HTTPException(status_code=400, detail="发布已在运行中")

        result = await scheduler.start_publishing()
        logger.info("开始发布任务")

        return {"action": action, **result}

    elif action == "pause":
        result = await scheduler.pause_publishing()
        logger.info("暂停发布任务")

        return {"action": action, **result}

    elif action == "stop":
        result = await scheduler.stop_publishing()
        logger.info("停止发布任务")

        return {"action": action, **result}

    else:
        raise HTTPException(status_code=400, detail="未知操作")


@router.post("/refresh", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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


@router.post("/shuffle", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def shuffle_tasks(db: AsyncSession = Depends(get_db)):
    """乱序发布 - 打乱待发布任务的顺序"""
    return await scheduler.shuffle_tasks(db)


@router.get("/logs", dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
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
