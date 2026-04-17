"""
Creative Phase B review API.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import ACTIVE_ROUTE_DEPENDENCIES
from models import get_db
from schemas import (
    CreativeApproveRequest,
    CreativeReviewActionResponse,
    CreativeRejectRequest,
    CreativeReworkRequest,
)
from services.creative_review_service import CreativeReviewError, CreativeReviewService
from services.creative_version_service import CreativeVersionService

router = APIRouter()


@router.post(
    "/{creative_id}/approve",
    response_model=CreativeReviewActionResponse,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
async def approve_creative(
    creative_id: int,
    request: CreativeApproveRequest,
    db: AsyncSession = Depends(get_db),
) -> CreativeReviewActionResponse:
    return await _execute_review_action(
        db,
        creative_id,
        action="approve",
        version_id=request.version_id,
        note=request.note,
    )


@router.post(
    "/{creative_id}/rework",
    response_model=CreativeReviewActionResponse,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
async def rework_creative(
    creative_id: int,
    request: CreativeReworkRequest,
    db: AsyncSession = Depends(get_db),
) -> CreativeReviewActionResponse:
    return await _execute_review_action(
        db,
        creative_id,
        action="rework",
        version_id=request.version_id,
        rework_type=request.rework_type,
        note=request.note,
    )


@router.post(
    "/{creative_id}/reject",
    response_model=CreativeReviewActionResponse,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
async def reject_creative(
    creative_id: int,
    request: CreativeRejectRequest,
    db: AsyncSession = Depends(get_db),
) -> CreativeReviewActionResponse:
    return await _execute_review_action(
        db,
        creative_id,
        action="reject",
        version_id=request.version_id,
        note=request.note,
    )


async def _execute_review_action(
    db: AsyncSession,
    creative_id: int,
    *,
    action: str,
    version_id: int,
    rework_type: str | None = None,
    note: str | None = None,
) -> CreativeReviewActionResponse:
    service = CreativeReviewService(db)
    try:
        if action == "approve":
            creative, check = await service.approve(creative_id, version_id=version_id, note=note)
        elif action == "rework":
            creative, check = await service.rework(
                creative_id,
                version_id=version_id,
                rework_type=rework_type,
                note=note,
            )
        elif action == "reject":
            creative, check = await service.reject(creative_id, version_id=version_id, note=note)
        else:
            raise ValueError(f"Unsupported creative review action: {action}")
    except CreativeReviewError as exc:
        await db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    await db.commit()
    await db.refresh(creative)
    await db.refresh(check)

    version_service = CreativeVersionService(db)
    return CreativeReviewActionResponse(
        creative_id=creative.id,
        creative_status=creative.status,
        current_version_id=creative.current_version_id,
        check=version_service.build_check_record_response(check),
    )
