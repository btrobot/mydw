"""
得物掘金工具 - 封面管理 API (SP1-03, SP8-02)
"""
import asyncio
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger
from pydantic import BaseModel, Field

from core.auth_dependencies import ACTIVE_ROUTE_DEPENDENCIES, GRACE_READONLY_ROUTE_DEPENDENCIES
from models import Cover, Video, get_db
from schemas import CoverResponse, BatchDeleteRequest, BatchDeleteResponse
from core.config import settings
from services.media_storage_service import MediaStorageService

router = APIRouter(tags=["封面管理"])

COVER_DIR = Path(settings.MATERIAL_BASE_PATH) / "cover"

# 允许的封面文件类型
ALLOWED_COVER_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_COVER_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/upload", response_model=CoverResponse, status_code=201, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def upload_cover(
    video_id: Optional[int] = Query(None, description="关联的视频ID"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> CoverResponse:
    """上传封面文件"""
    if file.content_type not in ALLOWED_COVER_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件类型，仅支持 JPEG/PNG/WebP")

    COVER_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name.replace("..", "")
    file_path = COVER_DIR / safe_name

    # 流式写入，累计大小，超限立即中断
    try:
        total_size = 0
        with file_path.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 256)  # 256KB chunks
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_COVER_SIZE:
                    f.close()
                    try:
                        file_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                    raise HTTPException(status_code=400, detail="文件过大，最大支持 20MB")
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("封面文件写入失败: filename={}, error={}", safe_name, str(e))
        raise HTTPException(status_code=500, detail="文件保存失败")

    cover = Cover(
        video_id=video_id,
        name=Path(file.filename).stem,
        file_path=str(file_path),
        file_size=total_size,
    )
    db.add(cover)
    await db.commit()
    await db.refresh(cover)
    logger.info("封面上传成功: cover_id={}, filename={}", cover.id, safe_name)
    return cover


@router.get("", response_model=list[CoverResponse], dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
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


@router.delete("/{cover_id}", status_code=204, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def delete_cover(
    cover_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除封面"""
    result = await db.execute(select(Cover).where(Cover.id == cover_id))
    cover = result.scalars().first()
    if not cover:
        raise HTTPException(status_code=404, detail="封面不存在")

    # 保存文件信息，用于删除 DB 记录后的引用计数检查
    file_path = cover.file_path
    file_hash = getattr(cover, "file_hash", None)

    await db.delete(cover)
    await db.commit()

    # 引用计数安全删除：仅当无其他记录引用同一 file_hash 时才删物理文件
    if file_path and file_hash:
        await MediaStorageService().safe_delete_async(file_path, file_hash, "covers", db)
    elif file_path:
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning("封面文件删除失败: cover_id={}, error={}", cover_id, str(e))

    logger.info("封面删除成功: cover_id={}", cover_id)


# ─── 批量删除 ────────────────────────────────────────────────────────────────

@router.post("/batch-delete", response_model=BatchDeleteResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def batch_delete_covers(
    data: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchDeleteResponse:
    """批量删除封面（清理物理文件）"""
    deleted = 0
    skipped_ids: List[int] = []

    # 收集待删文件信息，统一 commit 后再清理物理文件
    files_to_delete: List[tuple] = []

    for cover_id in data.ids:
        result = await db.execute(select(Cover).where(Cover.id == cover_id))
        cover = result.scalars().first()
        if not cover:
            skipped_ids.append(cover_id)
            continue

        files_to_delete.append((cover_id, cover.file_path, getattr(cover, "file_hash", None)))
        await db.delete(cover)
        deleted += 1

    await db.commit()

    for cover_id, file_path, file_hash in files_to_delete:
        if file_path and file_hash:
            await MediaStorageService().safe_delete_async(file_path, file_hash, "covers", db)
        elif file_path:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning("批量删除封面文件失败: cover_id={}, error={}", cover_id, str(e))

    logger.info("封面批量删除完成: deleted={}, skipped={}", deleted, len(skipped_ids))
    return BatchDeleteResponse(deleted=deleted, skipped=len(skipped_ids), skipped_ids=skipped_ids)


# ─── SP8-02: 封面自动提取 ────────────────────────────────────────────────────

class ExtractCoverRequest(BaseModel):
    video_id: int
    timestamp: float = Field(1.0, ge=0, description="截取时间点（秒）")


@router.post("/extract", response_model=CoverResponse, status_code=201, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def extract_cover(
    data: ExtractCoverRequest,
    db: AsyncSession = Depends(get_db),
) -> CoverResponse:
    """从视频指定时间点截取封面"""
    result = await db.execute(select(Video).where(Video.id == data.video_id))
    video = result.scalars().first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    if video.duration and data.timestamp > video.duration:
        raise HTTPException(status_code=400, detail="timestamp 超出视频时长 {:.1f}s".format(video.duration))
    if not Path(video.file_path).exists():
        raise HTTPException(status_code=400, detail="视频文件不存在")

    out_dir = Path(settings.MATERIAL_BASE_PATH) / "cover"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_name = "{}_{:.0f}s.jpg".format(Path(video.file_path).stem, data.timestamp)
    out_path = out_dir / out_name

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-ss", str(data.timestamp),
        "-i", video.file_path, "-frames:v", "1", "-q:v", "2",
        str(out_path),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
    if proc.returncode != 0 or not out_path.exists():
        logger.error("封面提取失败: video_id={}, stderr={}", data.video_id, stderr.decode()[:200])
        raise HTTPException(status_code=500, detail="封面提取失败")

    stat = out_path.stat()
    cover = Cover(video_id=data.video_id, file_path=str(out_path), file_size=stat.st_size)
    db.add(cover)
    await db.commit()
    await db.refresh(cover)
    logger.info("封面提取成功: cover_id={}, video_id={}", cover.id, data.video_id)
    return cover


# ─── 封面图片流 ───────────────────────────────────────────────────────────────

@router.get("/{cover_id}/image", dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def get_cover_image(
    cover_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """返回封面图片文件（FileResponse）"""
    result = await db.execute(select(Cover).where(Cover.id == cover_id))
    cover = result.scalars().first()
    if not cover:
        raise HTTPException(status_code=404, detail="封面不存在")

    file_path = Path(cover.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="封面文件不存在")

    # 根据扩展名推断 media_type
    suffix = file_path.suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    media_type = media_type_map.get(suffix, "application/octet-stream")

    logger.info("封面图片请求: cover_id={}", cover_id)
    return FileResponse(path=str(file_path), media_type=media_type, filename=file_path.name)
