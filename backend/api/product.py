"""
得物掘金工具 - 商品管理 API (SP1-06, SP7-04)
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from loguru import logger

from models import Product, Video, Cover, Copywriting, Topic, ProductTopic, get_db
from schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    ProductDetailResponse, CoverResponse, TopicResponse,
    VideoResponse, CopywritingResponse,
)
from services.product_parse_service import parse_and_create_materials
from utils.url_parser import extract_dewu_url

router = APIRouter(tags=["商品管理"])


def _build_detail_response(product: Product) -> ProductDetailResponse:
    """从已 eager-load 的 Product ORM 对象构建 ProductDetailResponse。"""
    videos = list(product.videos)
    # 封面：优先从 product.covers（直接 FK），兼容旧数据从 video.covers 收集
    direct_covers = list(product.covers)
    video_covers = [cover for video in videos for cover in video.covers]
    # 合并去重（以 id 为键）
    seen_ids: set[int] = set()
    all_covers: list[Cover] = []
    for c in direct_covers + video_covers:
        if c.id not in seen_ids:
            seen_ids.add(c.id)
            all_covers.append(c)

    return ProductDetailResponse(
        id=product.id,
        name=product.name,
        dewu_url=product.dewu_url,
        parse_status=product.parse_status,
        video_count=product.video_count,
        copywriting_count=product.copywriting_count,
        cover_count=product.cover_count,
        topic_count=product.topic_count,
        created_at=product.created_at,
        updated_at=product.updated_at,
        videos=[VideoResponse.model_validate(v) for v in videos],
        covers=[CoverResponse.model_validate(c) for c in all_covers],
        copywritings=[CopywritingResponse.model_validate(cw) for cw in product.copywritings],
        topics=[TopicResponse.model_validate(t) for t in product.topics],
    )


async def _load_product_detail(db: AsyncSession, product_id: int) -> Optional[Product]:
    """Eager-load 商品及全部关联素材，返回 ORM 对象或 None。"""
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.videos).selectinload(Video.covers),
            selectinload(Product.covers),
            selectinload(Product.copywritings),
            selectinload(Product.topics),
        )
    )
    return result.scalars().first()


@router.get("", response_model=ProductListResponse)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: Optional[str] = Query(None, description="按名称模糊搜索"),
    db: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    """获取商品列表（支持分页和名称搜索）"""
    query = select(Product)
    count_query = select(func.count()).select_from(Product)

    if name:
        query = query.where(Product.name.contains(name))
        count_query = count_query.where(Product.name.contains(name))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(Product.created_at.desc()).offset(skip).limit(limit)
    )
    items = result.scalars().all()

    return ProductListResponse(total=total, items=list(items))


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProductDetailResponse:
    """获取单个商品及其全部关联素材（videos、covers、copywritings、topics）"""
    product = await _load_product_detail(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return _build_detail_response(product)


@router.post("", response_model=ProductDetailResponse, status_code=201)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
) -> ProductDetailResponse:
    """创建商品并立即触发素材解析（原子操作）。

    流程：
    1. 从分享文本提取 dewu_url
    2. 检查 dewu_url 唯一性
    3. 创建 Product（parse_status='parsing'）
    4. 调用 parse_and_create_materials()
    5. 解析失败时设 parse_status='error'，仍返回商品（可重试）
    6. 返回 ProductDetailResponse
    """
    dewu_url = extract_dewu_url(data.share_text)
    if not dewu_url:
        raise HTTPException(status_code=422, detail="未找到有效的得物链接")

    existing = await db.execute(select(Product).where(Product.dewu_url == dewu_url))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="该得物链接已存在")

    product = Product(name=dewu_url, dewu_url=dewu_url, parse_status="parsing")
    db.add(product)
    await db.commit()
    await db.refresh(product)
    logger.info("商品创建成功，开始解析: product_id={}, dewu_url={}", product.id, dewu_url)

    try:
        await parse_and_create_materials(db=db, product=product)
    except Exception as e:
        logger.error("商品素材解析失败: product_id={}, error_type={}", product.id, type(e).__name__)
        # 解析失败：标记 error，保留商品供用户重试
        product.parse_status = "error"
        await db.commit()

    product = await _load_product_detail(db, product.id)
    return _build_detail_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """更新商品名称"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    if data.name is not None:
        product.name = data.name

    await db.commit()
    await db.refresh(product)
    logger.info("商品更新成功: product_id={}", product_id)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除商品，同时解除关联素材（保留素材记录，product_id 置 NULL）"""
    from sqlalchemy import update as sa_update

    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # 解除封面直接 FK
    await db.execute(
        sa_update(Cover).where(Cover.product_id == product_id).values(product_id=None)
    )
    # 解除视频关联封面的 product_id（通过 video 间接关联的封面）
    video_ids_result = await db.execute(
        select(Video.id).where(Video.product_id == product_id)
    )
    video_ids = video_ids_result.scalars().all()
    if video_ids:
        await db.execute(
            sa_update(Cover).where(Cover.video_id.in_(video_ids)).values(product_id=None)
        )
    # 解除视频和文案关联
    await db.execute(
        sa_update(Video).where(Video.product_id == product_id).values(product_id=None)
    )
    await db.execute(
        sa_update(Copywriting).where(Copywriting.product_id == product_id).values(product_id=None)
    )
    # product_topics 由 FK ondelete=CASCADE 自动清理
    await db.delete(product)
    await db.commit()
    logger.info("商品删除成功: product_id={}", product_id)


@router.post("/{product_id}/parse-materials", response_model=ProductDetailResponse)
async def parse_product_materials(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProductDetailResponse:
    """重新解析商品得物页面素材（封面、视频、标题、话题），覆盖更新已有素材记录"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    if not product.dewu_url:
        raise HTTPException(status_code=400, detail="商品未配置得物商品页 URL")

    product.parse_status = "parsing"
    await db.commit()
    await db.refresh(product)

    logger.info("触发商品素材重新解析: product_id={}", product_id)
    try:
        await parse_and_create_materials(db=db, product=product)
    except ValueError as e:
        product.parse_status = "error"
        await db.commit()
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("商品素材解析异常: product_id={}, error_type={}", product_id, type(e).__name__)
        product.parse_status = "error"
        await db.commit()
        raise HTTPException(status_code=500, detail="素材解析失败，请稍后重试")

    product = await _load_product_detail(db, product_id)
    return _build_detail_response(product)


@router.get("/{product_id}/covers", response_model=list[CoverResponse])
async def get_product_covers(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[CoverResponse]:
    """获取商品关联的所有封面"""
    product_result = await db.execute(select(Product).where(Product.id == product_id))
    if not product_result.scalars().first():
        raise HTTPException(status_code=404, detail="商品不存在")

    # 直接 FK 封面
    direct_result = await db.execute(
        select(Cover).where(Cover.product_id == product_id)
    )
    direct_covers = direct_result.scalars().all()

    # 通过 video 关联的封面（兼容旧数据）
    video_ids_result = await db.execute(
        select(Video.id).where(Video.product_id == product_id)
    )
    video_ids = video_ids_result.scalars().all()
    video_covers = []
    if video_ids:
        vc_result = await db.execute(
            select(Cover).where(Cover.video_id.in_(video_ids))
        )
        video_covers = vc_result.scalars().all()

    seen_ids: set[int] = set()
    all_covers = []
    for c in list(direct_covers) + list(video_covers):
        if c.id not in seen_ids:
            seen_ids.add(c.id)
            all_covers.append(c)

    return all_covers


@router.get("/{product_id}/topics", response_model=list[TopicResponse])
async def get_product_topics(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[TopicResponse]:
    """获取商品关联的话题（通过 product_topics 表）"""
    product_result = await db.execute(select(Product).where(Product.id == product_id))
    if not product_result.scalars().first():
        raise HTTPException(status_code=404, detail="商品不存在")

    topics_result = await db.execute(
        select(Topic)
        .join(ProductTopic, ProductTopic.topic_id == Topic.id)
        .where(ProductTopic.product_id == product_id)
    )
    return topics_result.scalars().all()
