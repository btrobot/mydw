"""
AI 剪辑服务 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
from loguru import logger

from core.auth_dependencies import ACTIVE_ROUTE_DEPENDENCIES
from services.ai_clip_service import AIClipService, ClipSegment, ClipResult

router = APIRouter()

# 全局 AI 剪辑服务实例
ai_clip_service = AIClipService()


# ============ 请求/响应模型 ============

class VideoInfoResponse(BaseModel):
    path: str
    duration: float
    width: int
    height: int
    fps: float
    size: int
    format: str


class ClipSegmentRequest(BaseModel):
    start: float
    end: float
    reason: str = ""


class SmartClipRequest(BaseModel):
    video_path: str
    segments: List[ClipSegmentRequest]
    output_path: str
    target_duration: int = 60


class AddAudioRequest(BaseModel):
    video_path: str
    audio_path: str
    output_path: str
    volume: float = 0.3


class AddCoverRequest(BaseModel):
    video_path: str
    cover_path: str
    output_path: str


class TrimVideoRequest(BaseModel):
    video_path: str
    start: float
    end: float
    output_path: str


class FullPipelineRequest(BaseModel):
    video_path: str
    audio_path: Optional[str] = None
    cover_path: Optional[str] = None
    target_duration: int = 60
    output_dir: Optional[str] = None


class DetectHighlightsResponse(BaseModel):
    segments: List[dict]
    count: int


class ClipResultResponse(BaseModel):
    success: bool
    output_path: Optional[str] = None
    duration: float = 0
    error: Optional[str] = None


# ============ API 端点 ============

@router.get("/video-info", response_model=VideoInfoResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def get_video_info(video_path: str) -> VideoInfoResponse:
    """获取视频信息"""
    info = await ai_clip_service.get_video_info(video_path)
    if not info:
        raise HTTPException(status_code=400, detail="无法获取视频信息，请检查文件是否存在")
    return VideoInfoResponse(
        path=info.path,
        duration=info.duration,
        width=info.width,
        height=info.height,
        fps=info.fps,
        size=info.size,
        format=info.format
    )


@router.get("/detect-highlights", response_model=DetectHighlightsResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def detect_highlights(video_path: str) -> DetectHighlightsResponse:
    """检测视频高光片段"""
    segments = await ai_clip_service.detect_highlights(video_path)
    return DetectHighlightsResponse(
        segments=[{"start": s.start, "end": s.end, "reason": s.reason} for s in segments],
        count=len(segments)
    )


@router.post("/smart-clip", response_model=ClipResultResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def smart_clip(request: SmartClipRequest) -> ClipResultResponse:
    """智能剪辑视频"""
    segments = [ClipSegment(**s.model_dump()) for s in request.segments]
    result = await ai_clip_service.smart_clip(
        request.video_path,
        segments,
        request.output_path,
        request.target_duration
    )
    return ClipResultResponse(
        success=result.success,
        output_path=result.output_path,
        duration=result.duration,
        error=result.error
    )


@router.post("/add-audio", response_model=ClipResultResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def add_audio(request: AddAudioRequest) -> ClipResultResponse:
    """添加背景音乐"""
    result = await ai_clip_service.add_audio(
        request.video_path,
        request.audio_path,
        request.output_path,
        request.volume
    )
    return ClipResultResponse(
        success=result.success,
        output_path=result.output_path,
        duration=result.duration,
        error=result.error
    )


@router.post("/add-cover", response_model=ClipResultResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def add_cover(request: AddCoverRequest) -> ClipResultResponse:
    """添加视频封面"""
    result = await ai_clip_service.add_cover(
        request.video_path,
        request.cover_path,
        request.output_path
    )
    return ClipResultResponse(
        success=result.success,
        output_path=result.output_path,
        duration=result.duration,
        error=result.error
    )


@router.post("/trim", response_model=ClipResultResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def trim_video(request: TrimVideoRequest) -> ClipResultResponse:
    """截取视频片段"""
    result = await ai_clip_service.trim_video(
        request.video_path,
        request.start,
        request.end,
        request.output_path
    )
    return ClipResultResponse(
        success=result.success,
        output_path=result.output_path,
        duration=result.duration,
        error=result.error
    )


@router.post("/full-pipeline", response_model=ClipResultResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def full_pipeline(request: FullPipelineRequest) -> ClipResultResponse:
    """
    完整 AI 剪辑流程
    1. 检测高光
    2. 智能剪辑
    3. 添加音频（可选）
    4. 添加封面（可选）
    """
    result, output_path = await ai_clip_service.full_pipeline(
        request.video_path,
        request.audio_path,
        request.cover_path,
        request.target_duration,
        request.output_dir
    )
    return ClipResultResponse(
        success=result.success,
        output_path=output_path,
        duration=result.duration,
        error=result.error
    )
