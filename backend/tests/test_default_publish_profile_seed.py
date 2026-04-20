from __future__ import annotations

import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

import main
from models import PublishProfile
from utils.local_ffmpeg_contract import (
    DEFAULT_LOCAL_FFMPEG_PARAMS,
    DEFAULT_LOCAL_FFMPEG_PARAMS_JSON,
)


@pytest.mark.asyncio
async def test_seed_default_publish_profile_creates_local_ffmpeg_default(
    engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(main._models, "async_session", session_factory)

    await main._seed_default_publish_profile()

    async with session_factory() as session:
        profiles = (await session.execute(select(PublishProfile))).scalars().all()

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.name == "默认合成配置"
    assert profile.is_default is True
    assert profile.composition_mode == "local_ffmpeg"
    assert profile.composition_params == DEFAULT_LOCAL_FFMPEG_PARAMS_JSON
    assert json.loads(profile.composition_params) == DEFAULT_LOCAL_FFMPEG_PARAMS


@pytest.mark.asyncio
async def test_seed_default_publish_profile_upgrades_legacy_default(
    engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(main._models, "async_session", session_factory)

    async with session_factory() as session:
        session.add(
            PublishProfile(
                name="默认配置",
                is_default=True,
                composition_mode="none",
                composition_params=None,
            )
        )
        await session.commit()

    await main._seed_default_publish_profile()

    async with session_factory() as session:
        profiles = (await session.execute(select(PublishProfile))).scalars().all()

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.name == "默认合成配置"
    assert profile.is_default is True
    assert profile.composition_mode == "local_ffmpeg"
    assert profile.composition_params == DEFAULT_LOCAL_FFMPEG_PARAMS_JSON
