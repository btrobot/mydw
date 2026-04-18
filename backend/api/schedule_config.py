"""
Canonical 调度配置 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import ACTIVE_ROUTE_DEPENDENCIES, GRACE_READONLY_ROUTE_DEPENDENCIES
from models import get_db
from schemas import ScheduleConfigRequest, ScheduleConfigResponse
from services.schedule_config_service import ScheduleConfigService

router = APIRouter()


def _to_schedule_config_response(config) -> ScheduleConfigResponse:
    return ScheduleConfigResponse.model_validate(
        {
            "id": config.id,
            "name": config.name,
            "start_hour": config.start_hour,
            "end_hour": config.end_hour,
            "interval_minutes": config.interval_minutes,
            "max_per_account_per_day": config.max_per_account_per_day,
            "shuffle": config.shuffle,
            "auto_start": config.auto_start,
            "publish_scheduler_mode": getattr(config, "publish_scheduler_mode", None) or "task",
            "publish_pool_kill_switch": bool(getattr(config, "publish_pool_kill_switch", False)),
            "publish_pool_shadow_read": bool(getattr(config, "publish_pool_shadow_read", False)),
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }
    )


@router.get("/schedule-config", response_model=ScheduleConfigResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def get_schedule_config(db: AsyncSession = Depends(get_db)):
    """获取 canonical 调度配置。"""
    service = ScheduleConfigService(db)
    return _to_schedule_config_response(await service.get_or_create_default())


@router.put("/schedule-config", response_model=ScheduleConfigResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def update_schedule_config(
    config_data: ScheduleConfigRequest,
    db: AsyncSession = Depends(get_db),
):
    """更新 canonical 调度配置。"""
    service = ScheduleConfigService(db)
    return _to_schedule_config_response(await service.update_default(config_data))
