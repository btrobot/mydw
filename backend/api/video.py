"""
得物掘金工具 - 视频管理 API (SP1-01, SP6-02, SP6-03)
"""
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from loguru import logger
from pydantic import BaseModel

from models import Video, Product, get_db
from schemas import VideoCreate, VideoUpdate, VideoResponse, VideoListResponse
from core.config import settings

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

    # 删除物理文件 (BUG-02 fix)
    if video.file_path:
        file_path = Path(video.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning("视频文件删除失败: video_id={}, error={}", video_id, str(e))

    await db.delete(video)
    await db.commit()
    logger.info("视频删除成功: video_id={}", video_id)


# ─── SP6-02: 视频文件上传 ────────────────────────────────────────────────────

ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime"}
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB


@router.post("/upload", response_model=VideoResponse, status_code=201)
async def upload_video(
    product_id: Optional[int] = Query(None, description="关联的商品ID"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> VideoResponse:
    """上传视频文件"""
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件类型，仅支持 MP4/MOV")

    content = await file.read()
    if len(content) > MAX_VIDEO_SIZE:
        raise HTTPException(status_code=400, detail="文件过大，最大支持 500MB")

    # 确定存储目录
    base = Path(settings.MATERIAL_BASE_PATH)
    if product_id:
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalars().first()
        if not product:
            raise HTTPException(status_code=400, detail="商品不存在")
        dest_dir = base / product.name
    else:
        dest_dir = base / "uncategorized"

    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename).name.replace("..", "")
    file_path = dest_dir / safe_name

    try:
        file_path.write_bytes(content)
    except Exception as e:
        logger.error("视频文件写入失败: filename={}, error={}", safe_name, str(e))
        raise HTTPException(status_code=500, detail="文件保存失败")

    video = Video(
        name=safe_name,
        file_path=str(file_path),
        product_id=product_id,
        file_size=len(content),
        source_type="upload",
    )
    db.add(video)
    await db.commit()
    video = await _get_video_with_product(db, video.id)
    logger.info("视频上传成功: video_id={}, filename={}", video.id, safe_name)
    return video


# ─── SP6-03: 目录扫描导入 ────────────────────────────────────────────────────

VIDEO_EXTENSIONS = {".mp4", ".mov"}


class ScanResult(BaseModel):
    """扫描导入结果"""
    total_scanned: int = 0
    new_imported: int = 0
    skipped: int = 0
    failed: int = 0
    details: List[str] = []


@router.post("/scan", response_model=ScanResult)
async def scan_videos(
    db: AsyncSession = Depends(get_db),
) -> ScanResult:
    """扫描 MATERIAL_BASE_PATH 下子目录，按商品名批量导入视频"""
    base = Path(settings.MATERIAL_BASE_PATH)
    if not base.exists():
        raise HTTPException(status_code=400, detail="素材目录不存在: {}".format(str(base)))

    result = ScanResult()

    # 遍历一级子目录（子目录名 = 商品名）
    for sub_dir in sorted(base.iterdir()):
        if not sub_dir.is_dir():
            continue
        # 跳过系统目录
        if sub_dir.name in ("audio", "cover", "uncategorized"):
            continue

        product_name = sub_dir.name

        # 查找或创建商品
        prod_result = await db.execute(
            select(Product).where(Product.name == product_name)
        )
        product = prod_result.scalars().first()
        if not product:
            product = Product(name=product_name)
            db.add(product)
            await db.flush()
            result.details.append("新建商品: {}".format(product_name))

        # 扫描视频文件
        for file_path in sorted(sub_dir.iterdir()):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in VIDEO_EXTENSIONS:
                continue

            result.total_scanned += 1
            str_path = str(file_path)

            # 基于 file_path 去重
            existing = await db.execute(
                select(Video).where(Video.file_path == str_path)
            )
            if existing.scalars().first():
                result.skipped += 1
                continue

            try:
                stat = file_path.stat()
                video = Video(
                    name=file_path.name,
                    file_path=str_path,
                    product_id=product.id,
                    file_size=stat.st_size,
                    source_type="scan",
                )
                db.add(video)
                result.new_imported += 1
            except Exception as e:
                result.failed += 1
                result.details.append("失败: {} - {}".format(file_path.name, str(e)))
                logger.warning("扫描导入失败: file={}, error={}", str_path, str(e))

    await db.commit()
    logger.info(
        "扫描导入完成: scanned={}, imported={}, skipped={}, failed={}",
        result.total_scanned, result.new_imported, result.skipped, result.failed,
    )
    return result
