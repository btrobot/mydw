"""
得物掘金工具 - 话题管理 API (SP1-05)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from models import Topic, get_db
from schemas import TopicCreate, TopicResponse, TopicListResponse

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
