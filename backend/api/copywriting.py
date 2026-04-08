"""
得物掘金工具 - 文案管理 API (SP1-02, SP7-03, SP7-04)
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from loguru import logger
from pydantic import BaseModel

from models import Copywriting, Task, get_db
from schemas import CopywritingCreate, CopywritingUpdate, CopywritingResponse, CopywritingListResponse

router = APIRouter(tags=["文案管理"])


async def _get_copywriting_with_product(db: AsyncSession, copywriting_id: int) -> Copywriting | None:
    result = await db.execute(
        select(Copywriting).options(selectinload(Copywriting.product)).where(Copywriting.id == copywriting_id)
    )
    return result.scalars().first()


@router.get("", response_model=CopywritingListResponse)
async def list_copywritings(
    product_id: Optional[int] = Query(None, description="按商品ID过滤"),
    source_type: Optional[str] = Query(None, description="按来源类型过滤"),
    keyword: Optional[str] = Query(None, description="按内容搜索"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> CopywritingListResponse:
    """获取文案列表（支持分页、商品和来源类型过滤）"""
    query = select(Copywriting)
    count_query = select(func.count()).select_from(Copywriting)

    if product_id is not None:
        query = query.where(Copywriting.product_id == product_id)
        count_query = count_query.where(Copywriting.product_id == product_id)
    if source_type is not None:
        query = query.where(Copywriting.source_type == source_type)
        count_query = count_query.where(Copywriting.source_type == source_type)
    if keyword:
        query = query.where(Copywriting.content.ilike(f"%{keyword}%"))
        count_query = count_query.where(Copywriting.content.ilike(f"%{keyword}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.options(selectinload(Copywriting.product)).order_by(Copywriting.created_at.desc()).offset(skip).limit(limit)
    )
    items = result.scalars().all()

    return CopywritingListResponse(total=total, items=list(items))


@router.get("/{copywriting_id}", response_model=CopywritingResponse)
async def get_copywriting(
    copywriting_id: int,
    db: AsyncSession = Depends(get_db),
) -> CopywritingResponse:
    """获取单个文案"""
    copywriting = await _get_copywriting_with_product(db, copywriting_id)
    if not copywriting:
        raise HTTPException(status_code=404, detail="文案不存在")
    return copywriting


@router.post("", response_model=CopywritingResponse, status_code=201)
async def create_copywriting(
    data: CopywritingCreate,
    db: AsyncSession = Depends(get_db),
) -> CopywritingResponse:
    """创建文案"""
    name = (data.name or "").strip() or data.content[:50]
    copywriting = Copywriting(
        name=name,
        content=data.content,
        product_id=data.product_id,
        source_type=data.source_type,
        source_ref=data.source_ref,
    )
    db.add(copywriting)
    await db.commit()
    copywriting = await _get_copywriting_with_product(db, copywriting.id)
    logger.info("文案创建成功: copywriting_id={}", copywriting.id)
    return copywriting


@router.put("/{copywriting_id}", response_model=CopywritingResponse)
async def update_copywriting(
    copywriting_id: int,
    data: CopywritingUpdate,
    db: AsyncSession = Depends(get_db),
) -> CopywritingResponse:
    """更新文案"""
    copywriting = await _get_copywriting_with_product(db, copywriting_id)
    if not copywriting:
        raise HTTPException(status_code=404, detail="文案不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(copywriting, field, value)

    await db.commit()
    copywriting = await _get_copywriting_with_product(db, copywriting_id)
    logger.info("文案更新成功: copywriting_id={}", copywriting_id)
    return copywriting


@router.delete("/{copywriting_id}", status_code=204)
async def delete_copywriting(
    copywriting_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除文案"""
    result = await db.execute(select(Copywriting).where(Copywriting.id == copywriting_id))
    copywriting = result.scalars().first()
    if not copywriting:
        raise HTTPException(status_code=404, detail="文案不存在")

    # SP7-04: 删除前引用检查
    ref_result = await db.execute(
        select(func.count()).select_from(Task).where(Task.copywriting_id == copywriting_id)
    )
    ref_count = ref_result.scalar() or 0
    if ref_count > 0:
        raise HTTPException(status_code=409, detail="文案被 {} 个任务引用，无法删除".format(ref_count))

    await db.delete(copywriting)
    await db.commit()
    logger.info("文案删除成功: copywriting_id={}", copywriting_id)


# ─── 批量删除 ────────────────────────────────────────────────────────────────

class BatchDeleteRequest(BaseModel):
    ids: List[int]


class BatchDeleteResponse(BaseModel):
    deleted: int
    skipped: int
    skipped_ids: List[int]


@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_copywritings(
    data: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchDeleteResponse:
    """批量删除文案（跳过被任务引用的）"""
    deleted = 0
    skipped_ids: List[int] = []

    for cw_id in data.ids:
        result = await db.execute(select(Copywriting).where(Copywriting.id == cw_id))
        copywriting = result.scalars().first()
        if not copywriting:
            skipped_ids.append(cw_id)
            continue

        ref_result = await db.execute(
            select(func.count()).select_from(Task).where(Task.copywriting_id == cw_id)
        )
        if (ref_result.scalar() or 0) > 0:
            skipped_ids.append(cw_id)
            continue

        await db.delete(copywriting)
        deleted += 1

    await db.commit()
    logger.info("文案批量删除完成: deleted={}, skipped={}", deleted, len(skipped_ids))
    return BatchDeleteResponse(deleted=deleted, skipped=len(skipped_ids), skipped_ids=skipped_ids)


# ─── SP7-03: 文案批量导入 ────────────────────────────────────────────────────

class ImportResult(BaseModel):
    total_lines: int = 0
    imported: int = 0
    skipped_empty: int = 0


@router.post("/import", response_model=ImportResult)
async def import_copywritings(
    product_id: Optional[int] = Query(None, description="关联的商品ID"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ImportResult:
    """从 .txt 文件批量导入文案（一行一条）"""
    if not file.filename or not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="仅支持 .txt 文件")

    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    lines = text.splitlines()

    result = ImportResult(total_lines=len(lines))
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.skipped_empty += 1
            continue
        cw = Copywriting(name=stripped[:50], content=stripped, product_id=product_id, source_type="import")
        db.add(cw)
        result.imported += 1

    await db.commit()
    logger.info("文案批量导入完成: imported={}, skipped={}", result.imported, result.skipped_empty)
    return result
