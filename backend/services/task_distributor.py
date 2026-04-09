"""
SP3-05: TaskDistributor — 多账号轮询分配任务
"""
from typing import List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from services.task_assembler import TaskAssembler
from models import Task


class TaskDistributor:
    """任务分发器：将视频列表按策略分配给多个账号"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def distribute(
        self,
        video_ids: List[int],
        account_ids: List[int],
        strategy: str = "round_robin",
        copywriting_mode: str = "auto_match",
        profile_id: Optional[int] = None,
        cover_id: Optional[int] = None,
        copywriting_ids: Optional[List[int]] = None,
        cover_ids: Optional[List[int]] = None,
        audio_ids: Optional[List[int]] = None,
    ) -> List[Task]:
        """
        将视频列表按策略分配给多个账号，每个视频创建一个任务。

        Args:
            video_ids: 视频 ID 列表
            account_ids: 账号 ID 列表（至少一个）
            strategy: 分配策略，目前支持 "round_robin"
            copywriting_mode: 文案匹配模式，透传给 TaskAssembler
            profile_id: 发布档案 ID，透传给 TaskAssembler
            cover_id: 封面 ID，透传给 TaskAssembler（向后兼容）
            copywriting_ids: 文案 ID 列表（素材篮模式）
            cover_ids: 封面 ID 列表（素材篮模式）
            audio_ids: 音频 ID 列表（素材篮模式）

        Returns:
            创建的 Task 列表
        """
        if not video_ids:
            logger.warning("TaskDistributor: video_ids 为空，跳过分配")
            return []

        if not account_ids:
            logger.warning("TaskDistributor: account_ids 为空，跳过分配")
            return []

        assembler = TaskAssembler(self.db)
        tasks: List[Task] = []

        # 按 account_id 分组，批量调用 assembler 减少 N+1
        groups: dict[int, List[int]] = {}
        for i, vid in enumerate(video_ids):
            acct = account_ids[i % len(account_ids)]
            groups.setdefault(acct, []).append(vid)

        for acct_id, vids in groups.items():
            result = await assembler.assemble(
                video_ids=vids,
                account_id=acct_id,
                copywriting_mode=copywriting_mode,
                profile_id=profile_id,
                cover_id=cover_id,
                copywriting_ids=copywriting_ids,
                cover_ids=cover_ids,
                audio_ids=audio_ids,
            )
            tasks.extend(result)
            logger.info(
                "TaskDistributor: account_id={} <- {} 个视频",
                acct_id,
                len(vids),
            )

        logger.info(
            "TaskDistributor: 分配完成, strategy={}, 视频数={}, 账号数={}, 任务数={}",
            strategy,
            len(video_ids),
            len(account_ids),
            len(tasks),
        )
        return tasks
