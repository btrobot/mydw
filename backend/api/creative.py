"""
Creative Phase 2 API.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import ACTIVE_ROUTE_DEPENDENCIES, GRACE_READONLY_ROUTE_DEPENDENCIES
from models import get_db
from schemas import (
    CreativeCreateRequest,
    CreativeDetailResponse,
    CreativeComposeSubmitResponse,
    CreativeStatus,
    CreativeUpdateRequest,
    CreativeWorkbenchListResponse,
    CreativeWorkbenchPoolState,
    CreativeWorkbenchSort,
)
from services.creative_service import CreativeService

router = APIRouter()


@router.get("", response_model=CreativeWorkbenchListResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def list_creatives(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    keyword: str | None = Query(None, min_length=1),
    status: CreativeStatus | None = Query(None),
    pool_state: CreativeWorkbenchPoolState | None = Query(None),
    sort: CreativeWorkbenchSort = Query(CreativeWorkbenchSort.UPDATED_DESC),
    recent_failures_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> CreativeWorkbenchListResponse:
    """Return the Creative workbench list with Phase 4 canonical orchestration metadata plus deprecated compatibility snapshot projections."""
    service = CreativeService(db)
    return await service.list_creatives(
        skip=skip,
        limit=limit,
        keyword=keyword,
        status=status,
        pool_state=pool_state,
        sort=sort,
        recent_failures_only=recent_failures_only,
    )


@router.post("", response_model=CreativeDetailResponse, status_code=201, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def create_creative(
    payload: CreativeCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> CreativeDetailResponse:
    """Create a creative using canonical input_items orchestration semantics while keeping legacy list carriers deprecated and write-blocked."""
    service = CreativeService(db)
    try:
        return await service.create_creative(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{creative_id}", response_model=CreativeDetailResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def get_creative(
    creative_id: int,
    db: AsyncSession = Depends(get_db),
) -> CreativeDetailResponse:
    """Return the Creative detail projection with canonical input_items/input_orchestration plus deprecated compatibility snapshot fields."""
    service = CreativeService(db)
    creative = await service.get_creative_detail(creative_id)
    if creative is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return creative


@router.patch("/{creative_id}", response_model=CreativeDetailResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def update_creative(
    creative_id: int,
    payload: CreativeUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> CreativeDetailResponse:
    """Update a creative using canonical input_items orchestration semantics while legacy list carriers remain deprecated compatibility-only projection."""
    service = CreativeService(db)
    try:
        creative = await service.update_creative(creative_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if creative is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return creative


@router.post(
    "/{creative_id}/submit-composition",
    response_model=CreativeComposeSubmitResponse,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
async def submit_creative_composition(
    creative_id: int,
    db: AsyncSession = Depends(get_db),
) -> CreativeComposeSubmitResponse:
    """Submit composition directly from the creative detail workflow."""
    service = CreativeService(db)
    try:
        return await service.submit_composition(creative_id)
    except ValueError as exc:
        detail = str(exc)
        if detail == "作品不存在":
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc
