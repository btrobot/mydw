"""
素材管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pathlib import Path
from loguru import logger

from models import Material
from models import get_db
from schemas import (
    MaterialCreate, MaterialUpdate, MaterialResponse,
    MaterialListResponse, MaterialType
)
from core.config import settings

router = APIRouter()

# 素材基础路径
MATERIAL_PATH = Path(settings.MATERIAL_BASE_PATH)


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
        content=material_data.content
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)

    logger.info(f"创建素材: {material.name} ({material.type})")
    return material


@router.post("/upload/{material_type}", response_model=MaterialResponse)
async def upload_material(
    material_type: MaterialType,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """上传素材文件"""
    # 创建素材目录
    type_dir = MATERIAL_PATH / material_type.value
    type_dir.mkdir(parents=True, exist_ok=True)

    # 保存文件
    file_path = type_dir / file.filename
    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    # 创建素材记录
    material = Material(
        type=material_type.value,
        name=file.filename,
        path=str(file_path),
        size=len(content)
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)

    logger.info(f"上传素材: {file.filename}")
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


@router.get("/path/{material_type}")
async def get_material_path(material_type: str):
    """获取素材类型目录"""
    type_dir = MATERIAL_PATH / material_type

    if not type_dir.exists():
        return {"path": str(MATERIAL_PATH), "files": []}

    # 列出目录下的文件
    files = []
    for f in type_dir.iterdir():
        if f.is_file():
            files.append({
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size
            })

    return {"path": str(type_dir), "files": files}


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取素材详情"""
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    return material


@router.put("/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: int,
    material_data: MaterialUpdate,
    db: AsyncSession = Depends(get_db)
):
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

    logger.info(f"更新素材: {material.name}")
    return material


@router.delete("/{material_id}", status_code=204)
async def delete_material(
    material_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除素材"""
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(status_code=404, detail="素材不存在")

    # 删除文件
    if material.path:
        file_path = Path(material.path)
        if file_path.exists():
            file_path.unlink()

    await db.delete(material)
    await db.commit()

    logger.info(f"删除素材: {material.name}")
    return None
