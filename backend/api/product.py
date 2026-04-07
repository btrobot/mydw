"""
得物掘金工具 - 商品管理 API (SP1-06)
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from models import Product, get_db
from schemas import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse

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
    """创建商品"""
    existing = await db.execute(select(Product).where(Product.name == data.name))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="商品名称已存在")

    product = Product(
        name=data.name,
        link=data.link,
        description=data.description,
        dewu_url=data.dewu_url,
        image_url=data.image_url,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    logger.info("商品创建成功: product_id={}, name={}", product.id, product.name)
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

    if data.name is not None and data.name != product.name:
        dup = await db.execute(select(Product).where(Product.name == data.name))
        if dup.scalars().first():
            raise HTTPException(status_code=400, detail="商品名称已存在")
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

    await db.delete(product)
    await db.commit()
    logger.info("商品删除成功: product_id={}", product_id)
