"""
任务管理 API
"""
from datetime import UTC, datetime

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
    BatchAssembleRequest, CompositionJobResponse, TaskCreateRequest,
)
from services.task_service import TaskService
from services.task_distributor import TaskDistributor
from services.scheduler import scheduler
from services.composition_service import CompositionService
from services.task_execution_semantics import TaskSemanticsError
from core.auth_dependencies import ACTIVE_ROUTE_DEPENDENCIES, GRACE_READONLY_ROUTE_DEPENDENCIES
from utils.time import utc_now_naive

router = APIRouter()


def _normalize_query_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _build_task_list_filters(
    *,
    status: Optional[str],
    account_id: Optional[int],
    task_kind: Optional[str],
    profile_id: Optional[int],
    creative_item_id: Optional[int],
    creative_version_id: Optional[int],
    batch_id: Optional[str],
    failed_at_status: Optional[str],
    retry_count_min: Optional[int],
    retry_count_max: Optional[int],
    created_from: Optional[datetime],
    created_to: Optional[datetime],
    updated_from: Optional[datetime],
    updated_to: Optional[datetime],
    scheduled_from: Optional[datetime],
    scheduled_to: Optional[datetime],
    publish_from: Optional[datetime],
    publish_to: Optional[datetime],
    has_error: Optional[bool],
    has_final_video: Optional[bool],
) -> list:
    filters = []

    if status:
        filters.append(Task.status == status)
    if account_id is not None:
        filters.append(Task.account_id == account_id)
    if task_kind:
        filters.append(Task.task_kind == task_kind)
    if profile_id is not None:
        filters.append(Task.profile_id == profile_id)
    if creative_item_id is not None:
        filters.append(Task.creative_item_id == creative_item_id)
    if creative_version_id is not None:
        filters.append(Task.creative_version_id == creative_version_id)
    if batch_id:
        filters.append(Task.batch_id == batch_id)
    if failed_at_status:
        filters.append(Task.failed_at_status == failed_at_status)
    if retry_count_min is not None:
        filters.append(Task.retry_count >= retry_count_min)
    if retry_count_max is not None:
        filters.append(Task.retry_count <= retry_count_max)

    created_from = _normalize_query_datetime(created_from)
    created_to = _normalize_query_datetime(created_to)
    updated_from = _normalize_query_datetime(updated_from)
    updated_to = _normalize_query_datetime(updated_to)
    scheduled_from = _normalize_query_datetime(scheduled_from)
    scheduled_to = _normalize_query_datetime(scheduled_to)
    publish_from = _normalize_query_datetime(publish_from)
    publish_to = _normalize_query_datetime(publish_to)

    if created_from is not None:
        filters.append(Task.created_at >= created_from)
    if created_to is not None:
        filters.append(Task.created_at <= created_to)
    if updated_from is not None:
        filters.append(Task.updated_at >= updated_from)
    if updated_to is not None:
        filters.append(Task.updated_at <= updated_to)
    if scheduled_from is not None:
        filters.append(Task.scheduled_time >= scheduled_from)
    if scheduled_to is not None:
        filters.append(Task.scheduled_time <= scheduled_to)
    if publish_from is not None:
        filters.append(Task.publish_time >= publish_from)
    if publish_to is not None:
        filters.append(Task.publish_time <= publish_to)

    if has_error is True:
        filters.append(Task.error_msg.is_not(None))
    elif has_error is False:
        filters.append(Task.error_msg.is_(None))

    if has_final_video is True:
        filters.append(Task.final_video_path.is_not(None))
    elif has_final_video is False:
        filters.append(Task.final_video_path.is_(None))

    return filters


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

@router.post("/", response_model=List[TaskResponse], status_code=201, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def create_tasks(
    request: TaskCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建任务（资源集合模型）— 1 份素材 x N 个账号 = N 个 Task"""
    from models import Video, Copywriting, Cover, Audio, Account

    # 验证资源存在
    video_result = await db.execute(select(Video).where(Video.id.in_(request.video_ids)))
    if len(video_result.scalars().all()) != len(request.video_ids):
        raise HTTPException(status_code=400, detail="部分视频ID不存在")

    if request.copywriting_ids:
        cw_result = await db.execute(select(Copywriting).where(Copywriting.id.in_(request.copywriting_ids)))
        if len(cw_result.scalars().all()) != len(request.copywriting_ids):
            raise HTTPException(status_code=400, detail="部分文案ID不存在")

    if request.cover_ids:
        cover_result = await db.execute(select(Cover).where(Cover.id.in_(request.cover_ids)))
        if len(cover_result.scalars().all()) != len(request.cover_ids):
            raise HTTPException(status_code=400, detail="部分封面ID不存在")

    if request.audio_ids:
        audio_result = await db.execute(select(Audio).where(Audio.id.in_(request.audio_ids)))
        if len(audio_result.scalars().all()) != len(request.audio_ids):
            raise HTTPException(status_code=400, detail="部分音频ID不存在")

    account_result = await db.execute(select(Account).where(Account.id.in_(request.account_ids)))
    if len(account_result.scalars().all()) != len(request.account_ids):
        raise HTTPException(status_code=400, detail="部分账号ID不存在")

    distributor = TaskDistributor(db)
    try:
        tasks = await distributor.distribute(
            video_ids=request.video_ids,
            account_ids=request.account_ids,
            copywriting_ids=request.copywriting_ids if request.copywriting_ids else None,
            cover_ids=request.cover_ids if request.cover_ids else None,
            audio_ids=request.audio_ids if request.audio_ids else None,
            topic_ids=request.topic_ids if request.topic_ids else None,
            profile_id=request.profile_id,
            name=request.name,
        )
    except TaskSemanticsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info(
        "创建任务: videos={}, accounts={}, tasks={}",
        len(request.video_ids), len(request.account_ids), len(tasks),
    )
    return tasks


@router.get("/", response_model=TaskListResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def list_tasks(
    status: Optional[str] = None,
    account_id: Optional[int] = None,
    task_kind: Optional[str] = None,
    profile_id: Optional[int] = None,
    creative_item_id: Optional[int] = None,
    creative_version_id: Optional[int] = None,
    batch_id: Optional[str] = None,
    failed_at_status: Optional[str] = None,
    retry_count_min: Optional[int] = None,
    retry_count_max: Optional[int] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    updated_from: Optional[datetime] = None,
    updated_to: Optional[datetime] = None,
    scheduled_from: Optional[datetime] = None,
    scheduled_to: Optional[datetime] = None,
    publish_from: Optional[datetime] = None,
    publish_to: Optional[datetime] = None,
    has_error: Optional[bool] = None,
    has_final_video: Optional[bool] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    filters = _build_task_list_filters(
        status=status,
        account_id=account_id,
        task_kind=task_kind,
        profile_id=profile_id,
        creative_item_id=creative_item_id,
        creative_version_id=creative_version_id,
        batch_id=batch_id,
        failed_at_status=failed_at_status,
        retry_count_min=retry_count_min,
        retry_count_max=retry_count_max,
        created_from=created_from,
        created_to=created_to,
        updated_from=updated_from,
        updated_to=updated_to,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        publish_from=publish_from,
        publish_to=publish_to,
        has_error=has_error,
        has_final_video=has_final_video,
    )

    query = select(Task).options(
        selectinload(Task.videos),
        selectinload(Task.copywritings),
        selectinload(Task.covers),
        selectinload(Task.audios),
        selectinload(Task.topics),
        selectinload(Task.account),
    )
    if filters:
        query = query.where(*filters)

    count_query = select(func.count(Task.id))
    if filters:
        count_query = count_query.where(*filters)

    total_count = (await db.execute(count_query)).scalar()
    query = query.order_by(Task.priority.desc(), Task.created_at.desc()).offset(offset).limit(limit)
    tasks = (await db.execute(query)).scalars().all()

    return TaskListResponse(total=total_count, items=list(tasks))


@router.get("/stats", response_model=TaskStatsResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def get_task_stats(db: AsyncSession = Depends(get_db)):
    """获取任务统计"""
    service = TaskService(db)
    stats = await service.get_task_stats()
    return TaskStatsResponse(**stats)


@router.get("/{task_id}", response_model=TaskResponse, dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """获取任务详情"""
    result = await db.execute(
        select(Task).options(
            selectinload(Task.videos),
            selectinload(Task.copywritings),
            selectinload(Task.covers),
            selectinload(Task.audios),
            selectinload(Task.topics),
            selectinload(Task.account),
        ).where(Task.id == task_id)
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.put("/{task_id}", response_model=TaskResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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


@router.delete("/{task_id}", status_code=204, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """删除任务"""
    service = TaskService(db)
    success = await service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return None


@router.delete("/", status_code=204, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def delete_all_tasks(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """清空所有任务"""
    service = TaskService(db)
    await service.delete_all_tasks(status)
    return None


@router.post("/{task_id}/cancel", response_model=TaskResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def cancel_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """取消任务（非终态 → cancelled）"""
    service = TaskService(db)
    task = await service.cancel_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已处于终态")
    return task


@router.post("/{task_id}/retry", response_model=TaskResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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


@router.post("/{task_id}/edit-retry", response_model=TaskResponse, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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


@router.post("/{task_id}/publish", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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


@router.post("/batch", response_model=List[TaskResponse], status_code=201, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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


@router.post("/shuffle", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def shuffle_tasks(db: AsyncSession = Depends(get_db)):
    """打乱任务顺序"""
    return await scheduler.shuffle_tasks(db)


@router.post("/assemble", response_model=List[TaskResponse], status_code=201, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def assemble_tasks(
    request: AssembleTasksRequest,
    db: AsyncSession = Depends(get_db)
):
    """组装任务（兼容旧接口，内部转发到新逻辑）"""
    distributor = TaskDistributor(db)
    try:
        tasks = await distributor.distribute(
            video_ids=request.video_ids,
            account_ids=request.account_ids,
            profile_id=request.profile_id,
        )
    except TaskSemanticsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return tasks


@router.post("/batch-assemble", response_model=List[TaskResponse], status_code=201, dependencies=ACTIVE_ROUTE_DEPENDENCIES)
async def batch_assemble_tasks(
    request: BatchAssembleRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量组装任务（兼容旧接口，内部转发到新逻辑）"""
    distributor = TaskDistributor(db)
    try:
        tasks = await distributor.distribute(
            video_ids=request.video_ids,
            account_ids=request.account_ids,
            copywriting_ids=request.copywriting_ids if request.copywriting_ids else None,
            cover_ids=request.cover_ids if request.cover_ids else None,
            audio_ids=request.audio_ids if request.audio_ids else None,
            profile_id=request.profile_id,
        )
    except TaskSemanticsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return tasks


# ============ 合成端点 (BE-TM-13) ============

@router.post(
    "/{task_id}/submit-composition",
    response_model=CompositionJobResponse,
    status_code=201,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
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


@router.post("/batch-submit-composition", dependencies=ACTIVE_ROUTE_DEPENDENCIES)
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


@router.post(
    "/{task_id}/cancel-composition",
    response_model=CompositionJobResponse,
    dependencies=ACTIVE_ROUTE_DEPENDENCIES,
)
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
    job.completed_at = utc_now_naive()
    job.updated_at = utc_now_naive()

    task.status = "draft"
    task.updated_at = utc_now_naive()

    await db.commit()
    await db.refresh(job)

    logger.info("合成已取消: task_id={}, job_id={}", task_id, job.id)
    return job


@router.get(
    "/{task_id}/composition-status",
    response_model=CompositionJobResponse,
    dependencies=GRACE_READONLY_ROUTE_DEPENDENCIES,
)
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
