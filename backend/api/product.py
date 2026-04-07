"""
得物掘金工具 - 商品管理 API (SP1-06, SP7-04)
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from models import Product, Video, Copywriting, get_db
from schemas import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse, ParseMaterialsResponse
from services.product_parse_service import parse_and_create_materials

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

    # SP7-04: 删除前引用检查
    video_count = (await db.execute(
        select(func.count()).select_from(Video).where(Video.product_id == product_id)
    )).scalar() or 0
    cw_count = (await db.execute(
        select(func.count()).select_from(Copywriting).where(Copywriting.product_id == product_id)
    )).scalar() or 0
    if video_count + cw_count > 0:
        raise HTTPException(
            status_code=409,
            detail="商品关联 {} 个视频和 {} 个文案，无法删除".format(video_count, cw_count),
        )

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
