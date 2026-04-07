"""
系统 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List
from datetime import datetime
from pathlib import Path
from loguru import logger

from models import Account, Task, Material, Product, SystemLog, PublishConfig
from models import get_db
from schemas import (
    SystemStats, SystemLogResponse, SystemLogListResponse,
    BackupRequest, ProductCreate, ProductResponse, ProductListResponse
)

router = APIRouter()


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    """获取系统统计"""
    # 账号统计
    total_accounts = await db.execute(select(func.count(Account.id)))
    active_accounts = await db.execute(
        select(func.count(Account.id)).where(Account.status == "active")
    )

    # 任务统计
    total_tasks = await db.execute(select(func.count(Task.id)))
    pending_tasks = await db.execute(
        select(func.count(Task.id)).where(Task.status == "pending")
    )
    success_tasks = await db.execute(
        select(func.count(Task.id)).where(Task.status == "success")
    )
    failed_tasks = await db.execute(
        select(func.count(Task.id)).where(Task.status == "failed")
    )

    # 素材统计
    total_materials = await db.execute(select(func.count(Material.id)))

    # 商品统计
    total_products = await db.execute(select(func.count(Product.id)))

    return SystemStats(
        total_accounts=total_accounts.scalar() or 0,
        active_accounts=active_accounts.scalar() or 0,
        total_tasks=total_tasks.scalar() or 0,
        pending_tasks=pending_tasks.scalar() or 0,
        success_tasks=success_tasks.scalar() or 0,
        failed_tasks=failed_tasks.scalar() or 0,
        total_materials=total_materials.scalar() or 0,
        total_products=total_products.scalar() or 0
    )


@router.get("/logs", response_model=SystemLogListResponse)
async def get_system_logs(
    level: str = None,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """获取系统日志"""
    query = select(SystemLog)

    if level:
        query = query.where(SystemLog.level == level.upper())

    query = query.order_by(desc(SystemLog.created_at)).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return SystemLogListResponse(total=len(logs), items=logs)


@router.post("/logs")
async def add_system_log(
    level: str,
    message: str,
    module: str = None,
    details: str = None,
    db: AsyncSession = Depends(get_db)
):
    """添加系统日志"""
    log = SystemLog(
        level=level.upper(),
        module=module,
        message=message,
        details=details
    )
    db.add(log)
    await db.commit()

    return {"success": True}


@router.get("/config")
async def get_system_config(db: AsyncSession = Depends(get_db)):
    """获取系统配置"""
    # TODO: 从配置文件读取
    return {
        "material_base_path": "D:/系统/桌面/得物剪辑/待上传数据",
        "auto_backup": False,
        "log_level": "INFO"
    }


@router.put("/config")
async def update_system_config(
    material_base_path: str = None,
    auto_backup: bool = None,
    log_level: str = None
):
    """更新系统配置"""
    # TODO: 保存到配置文件
    logger.info(f"更新系统配置: material_path={material_base_path}")

    return {"success": True}


@router.post("/backup")
async def backup_data(request: BackupRequest, db: AsyncSession = Depends(get_db)):
    """备份数据"""
    backup_dir = Path("data/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_{timestamp}.json"

    # TODO: 导出数据库到 JSON
    backup_data = {
        "version": "0.1.0",
        "timestamp": timestamp,
        "accounts": [],
        "tasks": [],
        "materials": [],
        "products": []
    }

    logger.info(f"数据备份: {backup_file}")

    return {
        "success": True,
        "backup_file": str(backup_file)
    }


# ============ 商品 API ============

@router.post("/products", response_model=ProductResponse, status_code=201, deprecated=True)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建商品"""
    product = Product(
        name=product_data.name,
        link=product_data.link
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    logger.info(f"创建商品: {product.name}")
    return product


@router.get("/products", response_model=ProductListResponse, deprecated=True)
async def list_products(db: AsyncSession = Depends(get_db)):
    """获取商品列表"""
    result = await db.execute(select(Product).order_by(Product.created_at.desc()))
    products = result.scalars().all()

    return ProductListResponse(total=len(products), items=products)


@router.delete("/products/{product_id}", status_code=204, deprecated=True)
async def delete_product(
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

    logger.info(f"删除商品: {product.name}")
    return None
