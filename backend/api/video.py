"""
得物掘金工具 - 视频管理 API (SP1-01)
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from loguru import logger

from models import Video, get_db
from schemas import VideoCreate, VideoUpdate, VideoResponse, VideoListResponse

router = APIRouter(tags=["视频管理"])


async def _get_video_with_product(db: AsyncSession, video_id: int) -> Video | None:
    result = await db.execute(
        select(Video).options(selectinload(Video.product)).where(Video.id == video_id)
    )
    return result.scalars().first()


@router.get("", response_model=VideoListResponse)
async def list_videos(
    product_id: Optional[int] = Query(None, description="按商品ID过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> VideoListResponse:
    """获取视频列表（支持分页和商品过滤）"""
    query = select(Video)
    count_query = select(func.count()).select_from(Video)

    if product_id is not None:
        query = query.where(Video.product_id == product_id)
        count_query = count_query.where(Video.product_id == product_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.options(selectinload(Video.product)).order_by(Video.created_at.desc()).offset(skip).limit(limit)
    )
    items = result.scalars().all()

    return VideoListResponse(total=total, items=list(items))


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """获取单个视频"""
    video = await _get_video_with_product(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    return video


@router.post("", response_model=VideoResponse, status_code=201)
async def create_video(
    data: VideoCreate,
    db: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """创建视频"""
    video = Video(
        name=data.name,
        file_path=data.file_path,
        product_id=data.product_id,
        file_size=data.file_size,
        duration=data.duration,
    )
    db.add(video)
    await db.commit()
    video = await _get_video_with_product(db, video.id)
    logger.info("视频创建成功: video_id={}, name={}", video.id, video.name)
    return video


@router.put("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    data: VideoUpdate,
    db: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """更新视频"""
    video = await _get_video_with_product(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    if data.name is not None:
        video.name = data.name
    if data.product_id is not None:
        video.product_id = data.product_id

    await db.commit()
    video = await _get_video_with_product(db, video_id)
    logger.info("视频更新成功: video_id={}", video_id)
    return video


@router.delete("/{video_id}", status_code=204)
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除视频"""
    video = await _get_video_with_product(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    await db.delete(video)
    await db.commit()
    logger.info("视频删除成功: video_id={}", video_id)
