"""
得物掘金工具 - 封面管理 API (SP1-03)
"""
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from models import Cover, get_db
from schemas import CoverResponse
from core.config import settings

router = APIRouter(tags=["封面管理"])

COVER_DIR = Path(settings.MATERIAL_BASE_PATH) / "cover"

# 允许的封面文件类型
ALLOWED_COVER_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_COVER_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/upload", response_model=CoverResponse, status_code=201)
async def upload_cover(
    video_id: Optional[int] = Query(None, description="关联的视频ID"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> CoverResponse:
    """上传封面文件"""
    if file.content_type not in ALLOWED_COVER_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件类型，仅支持 JPEG/PNG/WebP")

    content = await file.read()
    if len(content) > MAX_COVER_SIZE:
        raise HTTPException(status_code=400, detail="文件过大，最大支持 20MB")

    COVER_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name.replace("..", "")
    file_path = COVER_DIR / safe_name

    try:
        file_path.write_bytes(content)
    except Exception as e:
        logger.error("封面文件写入失败: filename={}, error={}", safe_name, str(e))
        raise HTTPException(status_code=500, detail="文件保存失败")

    cover = Cover(
        video_id=video_id,
        file_path=str(file_path),
        file_size=len(content),
    )
    db.add(cover)
    await db.commit()
    await db.refresh(cover)
    logger.info("封面上传成功: cover_id={}, filename={}", cover.id, safe_name)
    return cover


@router.get("", response_model=list[CoverResponse])
async def list_covers(
    video_id: Optional[int] = Query(None, description="按视频ID过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[CoverResponse]:
    """获取封面列表（支持分页和视频过滤）"""
    query = select(Cover)

    if video_id is not None:
        query = query.where(Cover.video_id == video_id)

    result = await db.execute(
        query.order_by(Cover.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.delete("/{cover_id}", status_code=204)
async def delete_cover(
    cover_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除封面"""
    result = await db.execute(select(Cover).where(Cover.id == cover_id))
    cover = result.scalars().first()
    if not cover:
        raise HTTPException(status_code=404, detail="封面不存在")

    if cover.file_path:
        file_path = Path(cover.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning("封面文件删除失败: cover_id={}, error={}", cover_id, str(e))

    await db.delete(cover)
    await db.commit()
    logger.info("封面删除成功: cover_id={}", cover_id)
