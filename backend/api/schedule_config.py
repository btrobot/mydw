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


@router.get("/schedule-config", response_model=ScheduleConfigResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def get_schedule_config(db: AsyncSession = Depends(get_db)):
    """获取 canonical 调度配置。"""
    service = ScheduleConfigService(db)
    return await service.get_or_create_default()


@router.put("/schedule-config", response_model=ScheduleConfigResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def update_schedule_config(
    config_data: ScheduleConfigRequest,
    db: AsyncSession = Depends(get_db),
):
    """更新 canonical 调度配置。"""
    service = ScheduleConfigService(db)
    return await service.update_default(config_data)
