"""
得物掘金工具 - 话题管理 API (SP1-05, SP4-03)
"""
import json
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from models import Topic, PublishConfig, get_db
from schemas import TopicCreate, TopicResponse, TopicListResponse, GlobalTopicRequest, GlobalTopicResponse

router = APIRouter(tags=["话题管理"])


@router.get("", response_model=TopicListResponse)
async def list_topics(
    sort: str = Query("created_at", description="排序字段: created_at | heat"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> TopicListResponse:
    """获取话题列表（支持分页和排序）"""
    query = select(Topic)
    count_query = select(func.count()).select_from(Topic)

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
    """设置全局话题（覆盖写入）"""
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

    # 读取或创建 PublishConfig（取第一条）
    cfg_result = await db.execute(select(PublishConfig).limit(1))
    config = cfg_result.scalars().first()
    if not config:
        config = PublishConfig()
        db.add(config)

    config.global_topic_ids = json.dumps(data.topic_ids)
    await db.commit()
    await db.refresh(config)

    logger.info("全局话题已更新: topic_ids={}", data.topic_ids)
    return GlobalTopicResponse(topic_ids=data.topic_ids, topics=list(found_topics))


@router.get("/global", response_model=GlobalTopicResponse)
async def get_global_topics(
    db: AsyncSession = Depends(get_db),
) -> GlobalTopicResponse:
    """获取当前全局话题列表"""
    cfg_result = await db.execute(select(PublishConfig).limit(1))
    config = cfg_result.scalars().first()

    if not config or not config.global_topic_ids:
        return GlobalTopicResponse(topic_ids=[], topics=[])

    try:
        raw = json.loads(config.global_topic_ids)
        topic_ids: List[int] = [tid for tid in raw if isinstance(tid, int)]
    except (ValueError, TypeError):
        topic_ids = []

    topics: list[Topic] = []
    if topic_ids:
        result = await db.execute(select(Topic).where(Topic.id.in_(topic_ids)))
        topics = list(result.scalars().all())

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
            topic.last_synced = datetime.utcnow()
        else:
            topic = Topic(
                name=item["name"],
                heat=item["heat"],
                source="search",
                last_synced=datetime.utcnow(),
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
