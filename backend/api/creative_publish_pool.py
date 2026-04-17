"""
Creative Phase C publish-pool read API.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import GRACE_READONLY_ROUTE_DEPENDENCIES
from models import get_db
from schemas import PublishPoolItemResponse, PublishPoolListResponse, PublishPoolStatus
from services.publish_pool_service import PublishPoolService

router = APIRouter()


@router.get(
    "",
    response_model=PublishPoolListResponse,
    dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES,
)
async def list_publish_pool_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: PublishPoolStatus | None = Query(default=PublishPoolStatus.ACTIVE),
    creative_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
) -> PublishPoolListResponse:
    service = PublishPoolService(db)
    return await service.list_pool_items(
        skip=skip,
        limit=limit,
        status=status,
        creative_id=creative_id,
    )


@router.get(
    "/{pool_item_id}",
    response_model=PublishPoolItemResponse,
    dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES,
)
async def get_publish_pool_item(
    pool_item_id: int,
    db: AsyncSession = Depends(get_db),
) -> PublishPoolItemResponse:
    service = PublishPoolService(db)
    pool_item = await service.get_pool_item(pool_item_id)
    if pool_item is None:
        raise HTTPException(status_code=404, detail="Publish pool item not found")
    return service.build_pool_item_response(pool_item)
