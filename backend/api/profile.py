"""
发布配置档 API
"""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import PublishProfile, get_db
from schemas import (
    PublishProfileCreate,
    PublishProfileUpdate,
    PublishProfileResponse,
    PublishProfileListResponse,
)
from services.topic_relation_service import get_profile_topic_ids, sync_profile_topic_ids

router = APIRouter()


@router.post("", response_model=PublishProfileResponse, status_code=201)
async def create_profile(
    data: PublishProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> PublishProfileResponse:
    """创建合成配置档；`global_topic_ids` 当前代表 profile-level default topics，并 dual-write 到 relation rows。"""
    # 检查名称唯一性
    existing = (await db.execute(
        select(PublishProfile).where(PublishProfile.name == data.name)
    )).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="配置档名称已存在")

    # 若新档设为默认，先清除其他默认
    if data.is_default:
        await _clear_default(db)

    profile = PublishProfile(
        name=data.name,
        is_default=data.is_default,
        composition_mode=data.composition_mode.value,
        coze_workflow_id=data.coze_workflow_id,
        composition_params=data.composition_params,
        global_topic_ids="[]",
        auto_retry=data.auto_retry,
        max_retry_count=data.max_retry_count,
    )
    db.add(profile)
    await db.flush()
    await sync_profile_topic_ids(db, profile, data.global_topic_ids)
    await db.commit()
    await db.refresh(profile)
    logger.info("配置档创建成功: id={}, name={}", profile.id, profile.name)
    return await _build_profile_response(profile, db)


@router.get("", response_model=PublishProfileListResponse)
async def list_profiles(
    db: AsyncSession = Depends(get_db),
) -> PublishProfileListResponse:
    """获取配置档列表；返回的 `global_topic_ids` 由 relation rows 优先解析。"""
    total_result = await db.execute(select(func.count()).select_from(PublishProfile))
    total = total_result.scalar_one()

    result = await db.execute(
        select(PublishProfile).order_by(PublishProfile.is_default.desc(), PublishProfile.created_at.asc())
    )
    profiles = result.scalars().all()
    items = [await _build_profile_response(p, db) for p in profiles]
    return PublishProfileListResponse(
        total=total,
        items=items,
    )


@router.get("/{profile_id}", response_model=PublishProfileResponse)
async def get_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
) -> PublishProfileResponse:
    """获取配置档详情；`global_topic_ids` 当前会被 TaskAssembler 自动并入任务，且 relation rows 优先。"""
    profile = await _get_or_404(db, profile_id)
    return await _build_profile_response(profile, db)


@router.put("/{profile_id}", response_model=PublishProfileResponse)
async def update_profile(
    profile_id: int,
    data: PublishProfileUpdate,
    db: AsyncSession = Depends(get_db),
) -> PublishProfileResponse:
    """更新配置档；`global_topic_ids` 会同步 relation rows 与 legacy JSON fallback。"""
    profile = await _get_or_404(db, profile_id)

    # 检查名称唯一性（排除自身）
    if data.name is not None and data.name != profile.name:
        conflict = (await db.execute(
            select(PublishProfile).where(
                PublishProfile.name == data.name,
                PublishProfile.id != profile_id,
            )
        )).scalars().first()
        if conflict:
            raise HTTPException(status_code=400, detail="配置档名称已存在")

    # 若设为默认，先清除其他默认
    if data.is_default is True and not profile.is_default:
        await _clear_default(db)

    if data.name is not None:
        profile.name = data.name
    if data.is_default is not None:
        profile.is_default = data.is_default
    if data.composition_mode is not None:
        profile.composition_mode = data.composition_mode.value
    if data.coze_workflow_id is not None:
        profile.coze_workflow_id = data.coze_workflow_id
    if data.composition_params is not None:
        profile.composition_params = data.composition_params
    if data.global_topic_ids is not None:
        await sync_profile_topic_ids(db, profile, data.global_topic_ids)
    if data.auto_retry is not None:
        profile.auto_retry = data.auto_retry
    if data.max_retry_count is not None:
        profile.max_retry_count = data.max_retry_count

    await db.commit()
    await db.refresh(profile)
    logger.info("配置档更新成功: id={}, name={}", profile.id, profile.name)
    return await _build_profile_response(profile, db)


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除配置档（默认配置档不允许删除）"""
    profile = await _get_or_404(db, profile_id)
    if profile.is_default:
        raise HTTPException(status_code=400, detail="默认配置档不允许删除")
    await db.delete(profile)
    await db.commit()
    logger.info("配置档删除成功: id={}", profile_id)


@router.put("/{profile_id}/set-default", response_model=PublishProfileResponse)
async def set_default_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
) -> PublishProfileResponse:
    """设为默认配置档（同时取消其他默认）"""
    profile = await _get_or_404(db, profile_id)
    await _clear_default(db)
    profile.is_default = True
    await db.commit()
    await db.refresh(profile)
    logger.info("已设为默认配置档: id={}, name={}", profile.id, profile.name)
    return await _build_profile_response(profile, db)


# ============ 内部辅助 ============

async def _get_or_404(db: AsyncSession, profile_id: int) -> PublishProfile:
    result = await db.execute(
        select(PublishProfile).where(PublishProfile.id == profile_id)
    )
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="配置档不存在")
    return profile


async def _clear_default(db: AsyncSession) -> None:
    """将所有配置档的 is_default 设为 False。"""
    result = await db.execute(
        select(PublishProfile).where(PublishProfile.is_default == True)  # noqa: E712
    )
    for p in result.scalars().all():
        p.is_default = False


async def _build_profile_response(
    profile: PublishProfile,
    db: AsyncSession,
) -> PublishProfileResponse:
    payload = {
        "id": profile.id,
        "name": profile.name,
        "is_default": profile.is_default,
        "composition_mode": profile.composition_mode,
        "coze_workflow_id": profile.coze_workflow_id,
        "composition_params": profile.composition_params,
        "global_topic_ids": await get_profile_topic_ids(db, profile),
        "auto_retry": profile.auto_retry,
        "max_retry_count": profile.max_retry_count,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }
    return PublishProfileResponse.model_validate(payload)
