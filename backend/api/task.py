"""
任务管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
from loguru import logger

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from models import Task, Account
from models import get_db
from schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    TaskPublishRequest, TaskBatchCreateRequest, AssembleTasksRequest
)
from services.task_service import TaskService
from services.task_distributor import TaskDistributor
from services.scheduler import scheduler

router = APIRouter()


# ============ 请求/响应模型 ============

class TaskStatsResponse(BaseModel):
    total: int
    pending: int
    running: int
    success: int
    failed: int
    paused: int
    today_success: int


class AutoGenerateRequest(BaseModel):
    account_id: int
    count: int = 10


# ============ API 端点 ============

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

    service = TaskService(db)
    task = await service.create_task(task_data.model_dump())
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
    query = select(Task).options(
        selectinload(Task.video),
        selectinload(Task.copywriting),
        selectinload(Task.topics),
        selectinload(Task.product),
    )
    if status:
        query = query.where(Task.status == status)
    if account_id:
        query = query.where(Task.account_id == account_id)

    count_query = select(func.count(Task.id))
    if status:
        count_query = count_query.where(Task.status == status)
    if account_id:
        count_query = count_query.where(Task.account_id == account_id)

    total_count = (await db.execute(count_query)).scalar()
    query = query.order_by(Task.priority.desc(), Task.created_at.desc()).offset(offset).limit(limit)
    tasks = (await db.execute(query)).scalars().all()

    return TaskListResponse(total=total_count, items=list(tasks))


@router.get("/stats", response_model=TaskStatsResponse)
async def get_task_stats(db: AsyncSession = Depends(get_db)):
    """获取任务统计"""
    service = TaskService(db)
    stats = await service.get_task_stats()
    return TaskStatsResponse(**stats)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务详情"""
    service = TaskService(db)
    task = await service.get_task(task_id)
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
    service = TaskService(db)
    update_dict = task_data.model_dump(exclude_unset=True)

    # 处理枚举类型
    if 'status' in update_dict and update_dict['status']:
        update_dict['status'] = update_dict['status'].value

    task = await service.update_task(task_id, update_dict)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """删除任务"""
    service = TaskService(db)
    success = await service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return None


@router.delete("/", status_code=204)
async def delete_all_tasks(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """清空所有任务"""
    service = TaskService(db)
    await service.delete_all_tasks(status)
    return None


@router.post("/{task_id}/publish")
async def publish_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """立即发布任务"""
    service = TaskService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "running":
        raise HTTPException(status_code=400, detail="任务正在发布中")

    # TODO: 添加到发布队列
    logger.info(f"任务 {task_id} 已添加到发布队列")
    return {"success": True, "message": "任务已添加到发布队列"}


@router.post("/batch", response_model=List[TaskResponse], status_code=201)
async def batch_create_tasks(
    batch_data: TaskBatchCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量创建任务"""
    service = TaskService(db)

    # 检查所有账号是否存在
    account_ids = set(t.account_id for t in batch_data.tasks)
    for aid in account_ids:
        result = await db.execute(select(Account).where(Account.id == aid))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"账号 {aid} 不存在")

    tasks_data = [t.model_dump() for t in batch_data.tasks]
    count, tasks = await service.create_tasks_batch(tasks_data)
    return tasks


@router.post("/auto-generate", deprecated=True)
async def auto_generate_tasks(
    request: AutoGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """自动生成任务"""
    # 检查账号
    result = await db.execute(
        select(Account).where(Account.id == request.account_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="账号不存在")

    service = TaskService(db)
    count, tasks = await service.auto_generate_tasks(
        request.account_id,
        count=request.count
    )

    return {
        "success": True,
        "message": f"自动生成 {count} 个任务",
        "count": count
    }


@router.post("/shuffle")
async def shuffle_tasks(db: AsyncSession = Depends(get_db)):
    """打乱任务顺序"""
    return await scheduler.shuffle_tasks(db)


@router.post("/init-from-materials", deprecated=True)
async def init_tasks_from_materials(
    account_id: int,
    count: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """从素材初始化任务"""
    # 检查账号
    result = await db.execute(select(Account).where(Account.id == account_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="账号不存在")

    service = TaskService(db)
    count, tasks = await service.init_from_materials(account_id, count=count)

    return {
        "success": True,
        "message": f"从素材初始化 {count} 个任务",
        "count": count
    }


@router.post("/assemble", response_model=List[TaskResponse], status_code=201)
async def assemble_tasks(
    request: AssembleTasksRequest,
    db: AsyncSession = Depends(get_db)
):
    """组装任务 — 多视频+多账号自动分配"""
    distributor = TaskDistributor(db)
    tasks = await distributor.distribute(
        video_ids=request.video_ids,
        account_ids=request.account_ids,
        strategy=request.strategy,
        copywriting_mode=request.copywriting_mode,
    )
    logger.info(
        "组装任务完成: video_count={}, account_count={}, task_count={}, strategy={}",
        len(request.video_ids),
        len(request.account_ids),
        len(tasks),
        request.strategy,
    )
    return tasks
