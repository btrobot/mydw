"""
得物掘金工具 - 话题管理 API (SP1-05, SP4-03)
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from models import Topic, TopicGroup, get_db
from schemas import (
    TopicCreate, TopicResponse, TopicListResponse,
    GlobalTopicRequest, GlobalTopicResponse,
    BatchDeleteRequest, BatchDeleteResponse,
    TopicGroupCreate, TopicGroupUpdate, TopicGroupResponse, TopicGroupListResponse,
)
from services.topic_relation_service import (
    get_global_topic_ids,
    get_topics_by_ids,
    get_topic_group_topic_ids,
    sync_global_topic_ids,
    sync_topic_group_topic_ids,
)

router = APIRouter(tags=["话题管理"])
group_router = APIRouter(tags=["话题组管理"])


@router.get("", response_model=TopicListResponse)
async def list_topics(
    sort: str = Query("created_at", description="排序字段: created_at | heat"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    keyword: str = Query(None, description="按名称模糊搜索"),
    source: str = Query(None, description="按来源精确过滤"),
    db: AsyncSession = Depends(get_db),
) -> TopicListResponse:
    """获取话题列表（支持分页、排序和过滤）"""
    query = select(Topic)
    count_query = select(func.count()).select_from(Topic)

    if keyword:
        query = query.where(Topic.name.ilike(f"%{keyword}%"))
        count_query = count_query.where(Topic.name.ilike(f"%{keyword}%"))
    if source:
        query = query.where(Topic.source == source)
        count_query = count_query.where(Topic.source == source)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    if sort == "heat":
        query = query.order_by(Topic.heat.desc())
    else:
        query = query.order_by(Topic.created_at.desc())

    result = await db.execute(query.offset(skip).limit(limit))
    items = result.scalars().all()

    return TopicListResponse(total=total, items=list(items))


@router.post("", response_model=TopicResponse, status_code=201)
async def create_topic(
    data: TopicCreate,
    db: AsyncSession = Depends(get_db),
) -> TopicResponse:
    """创建话题"""
    existing = await db.execute(select(Topic).where(Topic.name == data.name))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="话题名称已存在")

    topic = Topic(
        name=data.name,
        heat=data.heat,
        source=data.source,
    )
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    logger.info("话题创建成功: topic_id={}, name={}", topic.id, topic.name)
    return topic


@router.put("/global", response_model=GlobalTopicResponse)
async def set_global_topics(
    data: GlobalTopicRequest,
    db: AsyncSession = Depends(get_db),
) -> GlobalTopicResponse:
    """设置全局话题（canonical source=global_topics，仍 dual-write PublishConfig fallback；不会自动注入 task assembly）。"""
    # 验证所有 topic_id 存在
    if data.topic_ids:
        result = await db.execute(select(Topic).where(Topic.id.in_(data.topic_ids)))
        found_topics: List[Topic] = list(result.scalars().all())
        found_ids = {t.id for t in found_topics}
        missing = set(data.topic_ids) - found_ids
        if missing:
            raise HTTPException(status_code=400, detail=f"话题不存在: {sorted(missing)}")
    else:
        found_topics = []

    normalized = await sync_global_topic_ids(db, data.topic_ids)
    await db.commit()

    logger.info("全局话题已更新: topic_ids={}", normalized)
    return GlobalTopicResponse(topic_ids=normalized, topics=list(found_topics))


@router.get("/global", response_model=GlobalTopicResponse)
async def get_global_topics(
    db: AsyncSession = Depends(get_db),
) -> GlobalTopicResponse:
    """获取当前全局话题列表（relation rows 优先，缺失时 fallback 到 PublishConfig JSON）。"""
    topic_ids = await get_global_topic_ids(db)

    topics = await get_topics_by_ids(db, topic_ids)

    return GlobalTopicResponse(topic_ids=topic_ids, topics=topics)


@router.get("/search", response_model=TopicListResponse)
async def search_topics(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
) -> TopicListResponse:
    """搜索得物话题，结果自动入库（已存在则更新热度）"""
    from services.topic_service import TopicSearchService

    service = TopicSearchService()
    results = await service.search(keyword)

    for item in results:
        existing = await db.execute(select(Topic).where(Topic.name == item["name"]))
        topic = existing.scalars().first()
        if topic:
            topic.heat = item["heat"]
            topic.last_synced = datetime.now(datetime.UTC)
        else:
            topic = Topic(
                name=item["name"],
                heat=item["heat"],
                source="search",
                last_synced=datetime.now(datetime.UTC),
            )
            db.add(topic)

    await db.commit()

    # 返回入库后的话题（按热度降序）
    names = [item["name"] for item in results]
    if names:
        result = await db.execute(
            select(Topic).where(Topic.name.in_(names)).order_by(Topic.heat.desc())
        )
        topics = list(result.scalars().all())
    else:
        topics = []

    logger.info("话题搜索完成: keyword={}, found={}", keyword, len(topics))
    return TopicListResponse(total=len(topics), items=topics)


@router.delete("/{topic_id}", status_code=204)
async def delete_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除话题"""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalars().first()
    if not topic:
        raise HTTPException(status_code=404, detail="话题不存在")

    await db.delete(topic)
    await db.commit()
    logger.info("话题删除成功: topic_id={}", topic_id)


# ─── 批量删除 ────────────────────────────────────────────────────────────────

@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_topics(
    data: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchDeleteResponse:
    """批量删除话题"""
    deleted = 0
    skipped_ids: List[int] = []

    for topic_id in data.ids:
        result = await db.execute(select(Topic).where(Topic.id == topic_id))
        topic = result.scalars().first()
        if not topic:
            skipped_ids.append(topic_id)
            continue

        await db.delete(topic)
        deleted += 1

    await db.commit()
    logger.info("话题批量删除完成: deleted={}, skipped={}", deleted, len(skipped_ids))
    return BatchDeleteResponse(deleted=deleted, skipped=len(skipped_ids), skipped_ids=skipped_ids)


# ─── 话题组 CRUD ──────────────────────────────────────────────────────────────

@group_router.get("", response_model=TopicGroupListResponse)
async def list_topic_groups(
    db: AsyncSession = Depends(get_db),
) -> TopicGroupListResponse:
    """获取所有话题组；topic_ids 由 relation rows 优先解析，当前不自动注入 task assembly。"""
    result = await db.execute(select(TopicGroup).order_by(TopicGroup.created_at.desc()))
    groups = result.scalars().all()
    items = [await _build_group_response(group, db) for group in groups]
    return TopicGroupListResponse(total=len(groups), items=items)


@group_router.post("", response_model=TopicGroupResponse, status_code=201)
async def create_topic_group(
    data: TopicGroupCreate,
    db: AsyncSession = Depends(get_db),
) -> TopicGroupResponse:
    """创建话题组；当前只管理命名话题列表，并 dual-write relation rows + legacy JSON fallback。"""
    existing = await db.execute(select(TopicGroup).where(TopicGroup.name == data.name))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="话题组名称已存在")

    if data.topic_ids:
        found = await db.execute(select(Topic).where(Topic.id.in_(data.topic_ids)))
        found_ids = {t.id for t in found.scalars().all()}
        missing = set(data.topic_ids) - found_ids
        if missing:
            raise HTTPException(status_code=400, detail=f"话题不存在: {sorted(missing)}")

    group = TopicGroup(
        name=data.name,
        topic_ids="[]",
    )
    db.add(group)
    await db.flush()
    await sync_topic_group_topic_ids(db, group, data.topic_ids)
    await db.commit()
    await db.refresh(group)
    logger.info("话题组创建成功: group_id={}, name={}", group.id, group.name)
    return await _build_group_response(group, db)


@group_router.get("/{group_id}", response_model=TopicGroupResponse)
async def get_topic_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
) -> TopicGroupResponse:
    """获取话题组详情（含展开的话题列表）；relation rows 优先，当前不会自动注入 task assembly。"""
    result = await db.execute(select(TopicGroup).where(TopicGroup.id == group_id))
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="话题组不存在")
    return await _build_group_response(group, db)


@group_router.put("/{group_id}", response_model=TopicGroupResponse)
async def update_topic_group(
    group_id: int,
    data: TopicGroupUpdate,
    db: AsyncSession = Depends(get_db),
) -> TopicGroupResponse:
    """更新话题组；当前只影响 named topic-list CRUD surface，并同步 relation rows + legacy JSON fallback。"""
    result = await db.execute(select(TopicGroup).where(TopicGroup.id == group_id))
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="话题组不存在")

    if data.name is not None and data.name != group.name:
        dup = await db.execute(select(TopicGroup).where(TopicGroup.name == data.name))
        if dup.scalars().first():
            raise HTTPException(status_code=400, detail="话题组名称已存在")
        group.name = data.name

    if data.topic_ids is not None:
        if data.topic_ids:
            found = await db.execute(select(Topic).where(Topic.id.in_(data.topic_ids)))
            found_ids = {t.id for t in found.scalars().all()}
            missing = set(data.topic_ids) - found_ids
            if missing:
                raise HTTPException(status_code=400, detail=f"话题不存在: {sorted(missing)}")
        await sync_topic_group_topic_ids(db, group, data.topic_ids)

    await db.commit()
    await db.refresh(group)
    logger.info("话题组更新成功: group_id={}", group_id)
    return await _build_group_response(group, db)


@group_router.delete("/{group_id}", status_code=204)
async def delete_topic_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除话题组"""
    result = await db.execute(select(TopicGroup).where(TopicGroup.id == group_id))
    group = result.scalars().first()
    if not group:
        raise HTTPException(status_code=404, detail="话题组不存在")

    await db.delete(group)
    await db.commit()
    logger.info("话题组删除成功: group_id={}", group_id)


# ─── 内部辅助 ─────────────────────────────────────────────────────────────────

async def _build_group_response(group: TopicGroup, db: AsyncSession) -> TopicGroupResponse:
    """将 ORM TopicGroup 转换为 TopicGroupResponse（含展开话题）。"""
    topic_ids = await get_topic_group_topic_ids(db, group)

    topics = await get_topics_by_ids(db, topic_ids)

    return TopicGroupResponse(
        id=group.id,
        name=group.name,
        topic_ids=topic_ids,
        topics=topics,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )
