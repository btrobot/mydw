"""
Creative Phase A API.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import GRACE_READONLY_ROUTE_DEPENDENCIES
from models import get_db
from schemas import CreativeDetailResponse, CreativeWorkbenchListResponse
from services.creative_service import CreativeService

router = APIRouter()


@router.get("", response_model=CreativeWorkbenchListResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def list_creatives(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> CreativeWorkbenchListResponse:
    """Return the minimal Creative workbench list for Phase A."""
    service = CreativeService(db)
    return await service.list_creatives(skip=skip, limit=limit)


@router.get("/{creative_id}", response_model=CreativeDetailResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def get_creative(
    creative_id: int,
    db: AsyncSession = Depends(get_db),
) -> CreativeDetailResponse:
    """Return the minimal Creative detail projection for Phase A."""
    service = CreativeService(db)
    creative = await service.get_creative_detail(creative_id)
    if creative is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return creative
