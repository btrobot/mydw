"""
Creative workflow API for Phase D.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import ACTIVE_ROUTE_DEPENDENCIES
from models import get_db
from schemas import CreativeAIClipWorkflowResponse, CreativeAIClipWorkflowSubmitRequest
from services.ai_clip_workflow_service import AIClipWorkflowService, CreativeWorkflowError

router = APIRouter()


@router.post(
    "/{creative_id}/ai-clip/submit",
    response_model=CreativeAIClipWorkflowResponse,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
async def submit_ai_clip_workflow(
    creative_id: int,
    request: CreativeAIClipWorkflowSubmitRequest,
    db: AsyncSession = Depends(get_db),
) -> CreativeAIClipWorkflowResponse:
    service = AIClipWorkflowService(db)
    try:
        response = await service.submit_result(
            creative_id,
            source_version_id=request.source_version_id,
            output_path=request.output_path,
            title=request.title,
            workflow_type=request.workflow_type,
            metadata=request.metadata,
        )
    except CreativeWorkflowError as exc:
        await db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    await db.commit()
    return response
