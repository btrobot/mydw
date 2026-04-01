"""
任务管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from loguru import logger

from models import Task, Account
from models import get_db
from schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    TaskPublishRequest, TaskBatchCreateRequest
)

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建任务"""
    # 检查账号是否存在
    result = await db.execute(
        select(Account).where(Account.id == task_data.account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    task = Task(
        account_id=task_data.account_id,
        product_id=task_data.product_id,
        material_id=task_data.material_id,
        video_path=task_data.video_path,
        content=task_data.content,
        topic=task_data.topic,
        cover_path=task_data.cover_path,
        status="pending"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    logger.info(f"创建任务: ID={task.id}")
    return task


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    account_id: Optional[int] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    query = select(Task)

    if status:
        query = query.where(Task.status == status)
    if account_id:
        query = query.where(Task.account_id == account_id)

    # 获取总数
    count_query = select(func.count(Task.id))
    if status:
        count_query = count_query.where(Task.status == status)
    if account_id:
        count_query = count_query.where(Task.account_id == account_id)

    total = await db.execute(count_query)
    total_count = total.scalar()

    # 分页查询
    query = query.order_by(desc(Task.priority), Task.created_at)
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return TaskListResponse(total=total_count, items=tasks)


@router.get("/stats")
async def get_task_stats(db: AsyncSession = Depends(get_db)):
    """获取任务统计"""
    # 总数
    total = await db.execute(select(func.count(Task.id)))
    total_tasks = total.scalar()

    # 待发布
    pending = await db.execute(
        select(func.count(Task.id)).where(Task.status == "pending")
    )
    pending_tasks = pending.scalar()

    # 成功
    success = await db.execute(
        select(func.count(Task.id)).where(Task.status == "success")
    )
    success_tasks = success.scalar()

    # 失败
    failed = await db.execute(
        select(func.count(Task.id)).where(Task.status == "failed")
    )
    failed_tasks = failed.scalar()

    return {
        "total": total_tasks or 0,
        "pending": pending_tasks or 0,
        "success": success_tasks or 0,
        "failed": failed_tasks or 0
    }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    logger.info(f"更新任务: ID={task.id}")
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    await db.delete(task)
    await db.commit()

    logger.info(f"删除任务: ID={task_id}")
    return None


@router.delete("/", status_code=204)
async def delete_all_tasks(db: AsyncSession = Depends(get_db)):
    """清空所有任务"""
    await db.execute(select(Task).execution_options(synchronize_session="fetch"))
    await db.execute("DELETE FROM tasks")
    await db.commit()

    logger.warning("清空所有任务")
    return None


@router.post("/{task_id}/publish")
async def publish_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """立即发布任务"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "running":
        raise HTTPException(status_code=400, detail="任务正在发布中")

    # TODO: 将任务添加到发布队列

    return {"success": True, "message": "任务已添加到发布队列"}


@router.post("/batch", response_model=List[TaskResponse], status_code=201)
async def batch_create_tasks(
    batch_data: TaskBatchCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量创建任务"""
    tasks = []
    for task_data in batch_data.tasks:
        task = Task(
            account_id=task_data.account_id,
            product_id=task_data.product_id,
            material_id=task_data.material_id,
            video_path=task_data.video_path,
            content=task_data.content,
            topic=task_data.topic,
            cover_path=task_data.cover_path,
            status="pending"
        )
        db.add(task)
        tasks.append(task)

    await db.commit()

    # 刷新所有任务
    for task in tasks:
        await db.refresh(task)

    logger.info(f"批量创建任务: {len(tasks)} 个")
    return tasks
