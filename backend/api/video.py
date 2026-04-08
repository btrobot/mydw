"""
得物掘金工具 - 视频管理 API (SP1-01, SP6-02, SP6-03)
"""
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from starlette.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from loguru import logger
from pydantic import BaseModel

from models import Video, Product, Task, get_db
from schemas import VideoCreate, VideoUpdate, VideoResponse, VideoListResponse, BatchDeleteRequest, BatchDeleteResponse
from core.config import settings
from utils.ffprobe import extract_video_metadata
from utils.hash import compute_file_hash
from services.media_storage_service import MediaStorageService

router = APIRouter(tags=["视频管理"])


async def _get_video_with_product(db: AsyncSession, video_id: int) -> Video | None:
    result = await db.execute(
        select(Video).options(selectinload(Video.product)).where(Video.id == video_id)
    )
    return result.scalars().first()


@router.get("", response_model=VideoListResponse)
async def list_videos(
    product_id: Optional[int] = Query(None, description="按商品ID过滤"),
    keyword: Optional[str] = Query(None, description="按名称搜索"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> VideoListResponse:
    """获取视频列表（支持分页、商品过滤、关键词搜索）"""
    query = select(Video)
    count_query = select(func.count()).select_from(Video)

    if product_id is not None:
        query = query.where(Video.product_id == product_id)
        count_query = count_query.where(Video.product_id == product_id)
    if keyword:
        query = query.where(Video.name.ilike(f"%{keyword}%"))
        count_query = count_query.where(Video.name.ilike(f"%{keyword}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.options(selectinload(Video.product)).order_by(Video.created_at.desc()).offset(skip).limit(limit)
    )
    items = result.scalars().all()

    # 批量检查文件存在性，避免在 Pydantic validator 中做逐条 I/O
    responses = [VideoResponse.model_validate(item) for item in items]
    for resp in responses:
        resp.file_exists = Path(resp.file_path).exists()

    return VideoListResponse(total=total, items=responses)


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

    # SP7-04: 删除前引用检查
    ref_result = await db.execute(
        select(func.count()).select_from(Task).where(Task.video_id == video_id)
    )
    ref_count = ref_result.scalar() or 0
    if ref_count > 0:
        raise HTTPException(status_code=409, detail="视频被 {} 个任务引用，无法删除".format(ref_count))

    # 保存文件信息，用于删除 DB 记录后的引用计数检查
    file_path = video.file_path
    file_hash = video.file_hash

    await db.delete(video)
    await db.commit()

    # 引用计数安全删除：仅当无其他记录引用同一 file_hash 时才删物理文件
    if file_path and file_hash:
        await MediaStorageService().safe_delete_async(file_path, file_hash, "videos", db)
    elif file_path:
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning("视频文件删除失败: video_id={}, error={}", video_id, str(e))

    logger.info("视频删除成功: video_id={}", video_id)


# ─── 批量删除 ────────────────────────────────────────────────────────────────

@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_videos(
    data: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchDeleteResponse:
    """批量删除视频（跳过被任务引用的，清理物理文件）"""
    deleted = 0
    skipped_ids: List[int] = []

    # 收集待删文件信息，统一 commit 后再清理物理文件
    files_to_delete: List[tuple] = []

    for video_id in data.ids:
        video = await _get_video_with_product(db, video_id)
        if not video:
            skipped_ids.append(video_id)
            continue

        ref_result = await db.execute(
            select(func.count()).select_from(Task).where(Task.video_id == video_id)
        )
        if (ref_result.scalar() or 0) > 0:
            skipped_ids.append(video_id)
            continue

        files_to_delete.append((video_id, video.file_path, video.file_hash))
        await db.delete(video)
        deleted += 1

    await db.commit()

    for video_id, file_path, file_hash in files_to_delete:
        if file_path and file_hash:
            await MediaStorageService().safe_delete_async(file_path, file_hash, "videos", db)
        elif file_path:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning("批量删除视频文件失败: video_id={}, error={}", video_id, str(e))

    logger.info("视频批量删除完成: deleted={}, skipped={}", deleted, len(skipped_ids))
    return BatchDeleteResponse(deleted=deleted, skipped=len(skipped_ids), skipped_ids=skipped_ids)


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

    # 流式写入，累计大小，超限立即中断
    try:
        total_size = 0
        with file_path.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_VIDEO_SIZE:
                    f.close()
                    try:
                        file_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                    raise HTTPException(status_code=400, detail="文件过大，最大支持 500MB")
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("视频文件写入失败: filename={}, error={}", safe_name, str(e))
        raise HTTPException(status_code=500, detail="文件保存失败")

    file_size = total_size

    video = Video(
        name=safe_name,
        file_path=str(file_path),
        product_id=product_id,
        file_size=file_size,
        source_type="upload",
    )
    # SP7-01: FFprobe 元数据提取
    meta = await extract_video_metadata(str(file_path))
    video.duration = meta.duration
    video.width = meta.width
    video.height = meta.height
    # SP8-01: file_hash 去重
    file_hash = await compute_file_hash(str(file_path))
    if file_hash:
        dup_result = await db.execute(select(Video).where(Video.file_hash == file_hash))
        existing_video = dup_result.scalars().first()
        if existing_video:
            # 删除已写入的物理文件，阻止重复入库
            try:
                file_path.unlink()
            except Exception as unlink_err:
                logger.warning("重复视频物理文件删除失败: filename={}, error={}", safe_name, str(unlink_err))
            logger.info("视频重复已拒绝: hash={}, filename={}, existing_id={}", file_hash[:16], safe_name, existing_video.id)
            raise HTTPException(
                status_code=409,
                detail="视频已存在，existing_id={}".format(existing_video.id),
            )
    video.file_hash = file_hash
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
    skip_metadata: bool = Query(False, description="跳过 FFprobe 和 hash 计算，仅快速入库"),
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
                if skip_metadata:
                    video = Video(
                        name=file_path.name,
                        file_path=str_path,
                        product_id=product.id,
                        file_size=stat.st_size,
                        source_type="scan",
                    )
                else:
                    meta = await extract_video_metadata(str_path)
                    file_hash = await compute_file_hash(str_path)
                    video = Video(
                        name=file_path.name,
                        file_path=str_path,
                        product_id=product.id,
                        file_size=stat.st_size,
                        duration=meta.duration,
                        width=meta.width,
                        height=meta.height,
                        file_hash=file_hash,
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


# ─── SP7-02: 文件存在性批量校验 ──────────────────────────────────────────────

class ValidateResult(BaseModel):
    total: int = 0
    valid: int = 0
    missing: int = 0
    missing_ids: List[int] = []


@router.post("/validate", response_model=ValidateResult)
async def validate_videos(
    db: AsyncSession = Depends(get_db),
) -> ValidateResult:
    """批量校验视频文件是否存在"""
    result_obj = ValidateResult()
    videos_result = await db.execute(select(Video))
    for video in videos_result.scalars().all():
        result_obj.total += 1
        if Path(video.file_path).exists():
            result_obj.valid += 1
        else:
            result_obj.missing += 1
            result_obj.missing_ids.append(video.id)
    return result_obj


# ─── 视频流 ───────────────────────────────────────────────────────────────────

@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """流式返回视频文件"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalars().first()
    if not video or not video.file_path or not Path(video.file_path).exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    return FileResponse(video.file_path, media_type="video/mp4")
