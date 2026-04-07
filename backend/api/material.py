"""
素材管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from pathlib import Path
from pydantic import BaseModel
from loguru import logger

from models import Material, Product
from models import get_db
from schemas import (
    MaterialCreate, MaterialUpdate, MaterialResponse,
    MaterialListResponse, MaterialType,
    ProductCreate, ProductResponse, ProductListResponse,
)
from core.config import settings
from services.material_service import MaterialService

router = APIRouter()

# 素材基础路径
MATERIAL_PATH = Path(settings.MATERIAL_BASE_PATH)


# ============ 请求/响应模型 ============

class MaterialStatsResponse(BaseModel):
    video: dict
    text: dict
    cover: dict
    topic: dict
    audio: dict
    _total: dict


class ScanRequest(BaseModel):
    type: Optional[str] = None


class ScanResponse(BaseModel):
    total: int
    files: List[dict]


class ImportResponse(BaseModel):
    success: int
    failed: int
    total: int


class MaterialPathResponse(BaseModel):
    path: str
    files: List[dict]
    type: str


# ============ API 端点 ============

@router.post("/", response_model=MaterialResponse, status_code=201)
async def create_material(
    material_data: MaterialCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建素材"""
    material = Material(
        type=material_data.type.value,
        name=material_data.name,
        path=material_data.path,
        content=material_data.content,
        product_id=material_data.product_id
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)
    logger.info("创建素材: {}", material.name)
    return material


@router.post("/upload/{material_type}", response_model=MaterialResponse)
async def upload_material(
    material_type: MaterialType,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """上传素材文件"""
    type_dir = MATERIAL_PATH / material_type.value
    type_dir.mkdir(parents=True, exist_ok=True)

    file_path = type_dir / file.filename
    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    material = Material(
        type=material_type.value,
        name=file.filename,
        path=str(file_path),
        size=len(content)
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)
    logger.info("上传素材: {}", file.filename)
    return material


@router.get("/", response_model=MaterialListResponse)
async def list_materials(
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取素材列表"""
    query = select(Material)
    if type:
        query = query.where(Material.type == type)
    query = query.order_by(Material.created_at.desc())
    result = await db.execute(query)
    materials = result.scalars().all()
    return MaterialListResponse(total=len(materials), items=materials)


@router.get("/stats", response_model=MaterialStatsResponse)
async def get_material_stats(db: AsyncSession = Depends(get_db)):
    """获取素材统计"""
    service = MaterialService(db, str(MATERIAL_PATH))
    stats = await service.get_stats()
    default_stats = {'count': 0, 'size': 0}
    return MaterialStatsResponse(
        video=stats.get('video', default_stats),
        text=stats.get('text', default_stats),
        cover=stats.get('cover', default_stats),
        topic=stats.get('topic', default_stats),
        audio=stats.get('audio', default_stats),
        _total=stats.get('_total', default_stats)
    )


@router.get("/path/{material_type}", response_model=MaterialPathResponse)
async def get_material_path(material_type: str):
    """获取素材类型目录"""
    type_dir = MATERIAL_PATH / material_type
    if not type_dir.exists():
        type_dir.mkdir(parents=True, exist_ok=True)
        return MaterialPathResponse(path=str(MATERIAL_PATH), files=[], type=material_type)

    files = []
    for f in type_dir.iterdir():
        if f.is_file():
            files.append({
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size,
                "type": material_type
            })
    return MaterialPathResponse(path=str(type_dir), files=files, type=material_type)


@router.post("/scan", response_model=ScanResponse)
async def scan_materials(request: ScanRequest = None, db: AsyncSession = Depends(get_db)):
    """扫描本地素材目录"""
    material_type = request.type if request else None
    service = MaterialService(db, str(MATERIAL_PATH))
    files = await service.scan_directory(material_type)
    return ScanResponse(total=len(files), files=files)


@router.post("/import", response_model=ImportResponse)
async def import_materials(type: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """批量导入本地素材"""
    service = MaterialService(db, str(MATERIAL_PATH))
    success, failed = await service.import_directory(type)
    return ImportResponse(success=success, failed=failed, total=success + failed)


@router.post("/import/{material_type}", response_model=ImportResponse)
async def import_materials_by_type(material_type: str, db: AsyncSession = Depends(get_db)):
    """导入指定类型的素材"""
    service = MaterialService(db, str(MATERIAL_PATH))
    success, failed = await service.import_directory(material_type)
    return ImportResponse(success=success, failed=failed, total=success + failed)


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(material_id: int, db: AsyncSession = Depends(get_db)):
    """获取素材详情"""
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")
    return material


@router.get("/{material_id}/content")
async def get_material_content(material_id: int, db: AsyncSession = Depends(get_db)):
    """获取素材内容"""
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    if material.type not in ['text', 'topic']:
        raise HTTPException(status_code=400, detail="只有文本类素材可以获取内容")

    if not material.content and material.path:
        try:
            with open(material.path, 'r', encoding='utf-8') as f:
                material.content = f.read()
        except UnicodeDecodeError:
            try:
                with open(material.path, 'r', encoding='gbk') as f:
                    material.content = f.read()
            except Exception as e:
                logger.error("读取素材文件失败: material_id={}, error={}", material_id, str(e))
                raise HTTPException(status_code=500, detail="读取文件失败")

    return {"id": material.id, "name": material.name, "type": material.type, "content": material.content or ""}


@router.put("/{material_id}", response_model=MaterialResponse)
async def update_material(material_id: int, material_data: MaterialUpdate, db: AsyncSession = Depends(get_db)):
    """更新素材"""
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    update_data = material_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)
    await db.commit()
    await db.refresh(material)
    return material


@router.delete("/{material_id}", status_code=204)
async def delete_material(material_id: int, db: AsyncSession = Depends(get_db)):
    """删除素材"""
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    if material.path:
        file_path = Path(material.path)
        if file_path.exists():
            file_path.unlink()

    await db.delete(material)
    await db.commit()
    return None


@router.delete("/", status_code=204)
async def delete_all_materials(type: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """删除所有素材"""
    query = select(Material)
    if type:
        query = query.where(Material.type == type)
    result = await db.execute(query)
    materials = result.scalars().all()

    for material in materials:
        if material.path:
            file_path = Path(material.path)
            if file_path.exists():
                file_path.unlink()
        await db.delete(material)

    await db.commit()
    return None


# ============ 商品 API (迁移自 system.py) ============

@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product_material(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建商品"""
    product = Product(name=product_data.name, link=product_data.link)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    logger.info("创建商品: {}", product.name)
    return product


@router.get("/products", response_model=ProductListResponse)
async def list_products_material(db: AsyncSession = Depends(get_db)):
    """获取商品列表"""
    result = await db.execute(select(Product).order_by(Product.created_at.desc()))
    products = result.scalars().all()
    return ProductListResponse(total=len(products), items=products)


@router.delete("/products/{product_id}", status_code=204)
async def delete_product_material(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除商品"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    await db.delete(product)
    await db.commit()
    logger.info("删除商品: {}", product.name)
    return None
