"""
任务管理 API
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel, Field
from loguru import logger

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from models import Task, Account, CompositionJob
from models import get_db
from schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    TaskPublishRequest, TaskBatchCreateRequest, AssembleTasksRequest,
    BatchAssembleRequest, CompositionJobResponse,
)
from services.task_service import TaskService
from services.task_distributor import TaskDistributor
from services.scheduler import scheduler
from services.composition_service import CompositionService

router = APIRouter()


# ============ 请求/响应模型 ============

class TaskStatsResponse(BaseModel):
    total: int
    draft: int
    composing: int
    ready: int
    uploading: int
    uploaded: int
    failed: int
    cancelled: int
    today_uploaded: int


class BatchSubmitCompositionRequest(BaseModel):
    task_ids: List[int] = Field(..., min_length=1, description="任务ID列表")


# ============ API 端点 ============

@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建任务"""
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
        selectinload(Task.cover),
        selectinload(Task.audio),
        selectinload(Task.account),
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
    result = await db.execute(
        select(Task).options(
            selectinload(Task.video),
            selectinload(Task.copywriting),
            selectinload(Task.topics),
            selectinload(Task.product),
            selectinload(Task.cover),
            selectinload(Task.audio),
            selectinload(Task.account),
        ).where(Task.id == task_id)
    )
    task = result.scalars().first()
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


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """取消任务（非终态 → cancelled）"""
    service = TaskService(db)
    task = await service.cancel_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已处于终态")
    return task


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def quick_retry_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """快速重试：failed → failed_at_status 对应状态"""
    service = TaskService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    try:
        result = await service.quick_retry(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/{task_id}/edit-retry", response_model=TaskResponse)
async def edit_retry_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """编辑重试：failed → draft"""
    service = TaskService(db)
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    try:
        result = await service.edit_retry(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


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

    if task.status == "uploading":
        raise HTTPException(status_code=400, detail="任务正在发布中")

    logger.info("任务 {} 已添加到发布队列", task_id)
    return {"success": True, "message": "任务已添加到发布队列"}


@router.post("/batch", response_model=List[TaskResponse], status_code=201)
async def batch_create_tasks(
    batch_data: TaskBatchCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量创建任务"""
    service = TaskService(db)

    account_ids = set(t.account_id for t in batch_data.tasks)
    for aid in account_ids:
        result = await db.execute(select(Account).where(Account.id == aid))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"账号 {aid} 不存在")

    tasks_data = [t.model_dump() for t in batch_data.tasks]
    count, tasks = await service.create_tasks_batch(tasks_data)
    return tasks


@router.post("/shuffle")
async def shuffle_tasks(db: AsyncSession = Depends(get_db)):
    """打乱任务顺序"""
    return await scheduler.shuffle_tasks(db)


@router.post("/assemble", response_model=List[TaskResponse], status_code=201)
async def assemble_tasks(
    request: AssembleTasksRequest,
    db: AsyncSession = Depends(get_db)
):
    """组装任务 — 多视频+多账号自动分配（已废弃，使用 /batch-assemble）"""
    distributor = TaskDistributor(db)
    tasks = await distributor.distribute(
        video_ids=request.video_ids,
        account_ids=request.account_ids,
        strategy=request.strategy,
        copywriting_mode=request.copywriting_mode,
        profile_id=request.profile_id,
        cover_id=request.cover_id,
    )
    logger.info(
        "组装任务完成: video_count={}, account_count={}, task_count={}, strategy={}",
        len(request.video_ids),
        len(request.account_ids),
        len(tasks),
        request.strategy,
    )
    return tasks


@router.post("/batch-assemble", response_model=List[TaskResponse], status_code=201)
async def batch_assemble_tasks(
    request: BatchAssembleRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量组装任务 — 素材篮模型（视频+文案+封面+音频+账号）"""
    from models import Video, Copywriting, Cover, Audio, Account

    # 验证所有 ID 存在
    video_result = await db.execute(select(Video).where(Video.id.in_(request.video_ids)))
    videos = video_result.scalars().all()
    if len(videos) != len(request.video_ids):
        raise HTTPException(status_code=400, detail="部分视频ID不存在")

    if request.copywriting_ids:
        cw_result = await db.execute(select(Copywriting).where(Copywriting.id.in_(request.copywriting_ids)))
        copywritings = cw_result.scalars().all()
        if len(copywritings) != len(request.copywriting_ids):
            raise HTTPException(status_code=400, detail="部分文案ID不存在")

    if request.cover_ids:
        cover_result = await db.execute(select(Cover).where(Cover.id.in_(request.cover_ids)))
        covers = cover_result.scalars().all()
        if len(covers) != len(request.cover_ids):
            raise HTTPException(status_code=400, detail="部分封面ID不存在")

    if request.audio_ids:
        audio_result = await db.execute(select(Audio).where(Audio.id.in_(request.audio_ids)))
        audios = audio_result.scalars().all()
        if len(audios) != len(request.audio_ids):
            raise HTTPException(status_code=400, detail="部分音频ID不存在")

    account_result = await db.execute(select(Account).where(Account.id.in_(request.account_ids)))
    accounts = account_result.scalars().all()
    if len(accounts) != len(request.account_ids):
        raise HTTPException(status_code=400, detail="部分账号ID不存在")

    # 调用 TaskDistributor 分配任务
    distributor = TaskDistributor(db)
    tasks = await distributor.distribute(
        video_ids=request.video_ids,
        account_ids=request.account_ids,
        strategy=request.strategy,
        copywriting_mode=request.copywriting_mode,
        profile_id=request.profile_id,
        copywriting_ids=request.copywriting_ids if request.copywriting_ids else None,
        cover_ids=request.cover_ids if request.cover_ids else None,
        audio_ids=request.audio_ids if request.audio_ids else None,
    )

    logger.info(
        "素材篮组装完成: video_count={}, copywriting_count={}, cover_count={}, audio_count={}, account_count={}, task_count={}",
        len(request.video_ids),
        len(request.copywriting_ids),
        len(request.cover_ids),
        len(request.audio_ids),
        len(request.account_ids),
        len(tasks),
    )
    return tasks


# ============ 合成端点 (BE-TM-13) ============

@router.post("/{task_id}/submit-composition", response_model=CompositionJobResponse, status_code=201)
async def submit_composition(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> CompositionJobResponse:
    """提交单个任务合成（draft → composing）"""
    service = CompositionService(db)
    try:
        job = await service.submit_composition(task_id)
        logger.info("合成提交成功: task_id={}, job_id={}", task_id, job.id)
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("合成提交失败: task_id={}, error_type={}", task_id, type(e).__name__)
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/batch-submit-composition")
async def batch_submit_composition(
    request: BatchSubmitCompositionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """批量提交合成任务"""
    service = CompositionService(db)
    result = await service.batch_submit(request.task_ids)
    logger.info(
        "批量合成提交: total={}, success={}, failed={}",
        len(request.task_ids),
        result["success_count"],
        result["failed_count"],
    )
    return result


@router.post("/{task_id}/cancel-composition", response_model=CompositionJobResponse)
async def cancel_composition(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> CompositionJobResponse:
    """取消合成（composing → draft，CompositionJob 标记 cancelled）"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "composing":
        raise HTTPException(status_code=400, detail=f"任务当前状态为 {task.status}，只有 composing 状态可取消合成")

    if not task.composition_job_id:
        raise HTTPException(status_code=400, detail="任务没有关联的合成任务")

    job_result = await db.execute(
        select(CompositionJob).where(CompositionJob.id == task.composition_job_id)
    )
    job = job_result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="合成任务不存在")

    job.status = "cancelled"
    job.completed_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()

    task.status = "draft"
    task.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(job)

    logger.info("合成已取消: task_id={}, job_id={}", task_id, job.id)
    return job


@router.get("/{task_id}/composition-status", response_model=CompositionJobResponse)
async def get_composition_status(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> CompositionJobResponse:
    """查询任务合成状态"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if not task.composition_job_id:
        raise HTTPException(status_code=404, detail="任务没有关联的合成任务")

    job_result = await db.execute(
        select(CompositionJob).where(CompositionJob.id == task.composition_job_id)
    )
    job = job_result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="合成任务不存在")

    return job
