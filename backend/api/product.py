"""
得物掘金工具 - 商品管理 API (SP1-06, SP7-04)
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from loguru import logger

from models import Product, Video, Copywriting, get_db
from schemas import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse, ParseMaterialsResponse
from services.product_parse_service import parse_and_create_materials
from utils.url_parser import extract_dewu_url

router = APIRouter(tags=["商品管理"])


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


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """获取单个商品"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return product


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """创建商品 — 从分享文本解析得物链接，以 dewu_url 查重"""
    dewu_url = extract_dewu_url(data.share_text)
    if not dewu_url:
        raise HTTPException(status_code=422, detail="未找到有效的得物链接")

    existing = await db.execute(select(Product).where(Product.dewu_url == dewu_url))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="该得物链接已存在")

    product = Product(name=dewu_url, dewu_url=dewu_url)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    logger.info("商品创建成功: product_id={}, dewu_url={}", product.id, dewu_url)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """更新商品"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    if data.name is not None:
        product.name = data.name

    if data.link is not None:
        product.link = data.link
    if data.description is not None:
        product.description = data.description
    if data.dewu_url is not None:
        product.dewu_url = data.dewu_url
    if data.image_url is not None:
        product.image_url = data.image_url

    await db.commit()
    await db.refresh(product)
    logger.info("商品更新成功: product_id={}", product_id)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除商品"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # D-4: 解除关联素材（保留素材记录，将 product_id 置 NULL）
    await db.execute(
        update(Video).where(Video.product_id == product_id).values(product_id=None)
    )
    await db.execute(
        update(Copywriting).where(Copywriting.product_id == product_id).values(product_id=None)
    )
    # product_topics 由 FK ondelete=CASCADE 自动清理
    await db.delete(product)
    await db.commit()
    logger.info("商品删除成功: product_id={}", product_id)


@router.post("/{product_id}/parse-materials", response_model=ParseMaterialsResponse)
async def parse_product_materials(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> ParseMaterialsResponse:
    """解析商品得物页面素材（封面、视频、标题、话题），覆盖更新已有素材记录"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    if not product.dewu_url:
        raise HTTPException(status_code=400, detail="商品未配置得物商品页 URL")

    logger.info("触发商品素材解析: product_id={}", product_id)
    try:
        data = await parse_and_create_materials(db=db, product=product)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("商品素材解析异常: product_id={}, error_type={}", product_id, type(e).__name__)
        raise HTTPException(status_code=500, detail="素材解析失败，请稍后重试")

    return ParseMaterialsResponse(**data)
