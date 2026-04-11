"""
调度配置访问服务

目的：
- 为 ScheduleConfig 提供单一访问入口
- 作为后续从 PublishConfig 迁移到 canonical schedule-config contract 的地基
- 兼容读取历史 PublishConfig 数据，但后续写入统一落到 ScheduleConfig
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import PublishConfig, ScheduleConfig


class ScheduleConfigService:
    """ScheduleConfig 访问服务。"""

    DEFAULT_NAME = "default"
    MUTABLE_FIELDS = (
        "start_hour",
        "end_hour",
        "interval_minutes",
        "max_per_account_per_day",
        "shuffle",
        "auto_start",
    )

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_default(self) -> Optional[ScheduleConfig]:
        """读取默认调度配置；不存在时返回 None。"""
        result = await self.db.execute(
            select(ScheduleConfig).where(ScheduleConfig.name == self.DEFAULT_NAME)
        )
        return result.scalar_one_or_none()

    async def get_legacy_default(self) -> Optional[PublishConfig]:
        """读取遗留 publish_config 默认记录（兼容迁移兜底）。"""
        result = await self.db.execute(
            select(PublishConfig).where(PublishConfig.name == self.DEFAULT_NAME)
        )
        return result.scalar_one_or_none()

    async def get_or_create_default(self) -> ScheduleConfig:
        """
        获取默认调度配置；如果不存在则创建一条默认记录。

        该方法为后续 canonical API 收口准备，在 PR1 中主要用于单元测试和后续接入。
        """
        config = await self.get_default()
        if config:
            return config

        legacy = await self.get_legacy_default()
        config = ScheduleConfig(name=self.DEFAULT_NAME)
        if legacy:
            for field in self.MUTABLE_FIELDS:
                setattr(config, field, getattr(legacy, field))

        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def update_default(self, config_data: Any) -> ScheduleConfig:
        """更新默认调度配置，并返回最新记录。"""
        config = await self.get_or_create_default()
        for field in self.MUTABLE_FIELDS:
            setattr(config, field, getattr(config_data, field))

        await self.db.commit()
        await self.db.refresh(config)
        return config
