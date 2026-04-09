"""
TaskDistributor — 1 份素材集合 x N 个账号 = N 个 Task
"""
from typing import List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from models import Task
from services.task_assembler import TaskAssembler


class TaskDistributor:
    """为每个账号创建一个 Task，关联相同的素材集合"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def distribute(
        self,
        video_ids: List[int],
        account_ids: List[int],
        copywriting_ids: Optional[List[int]] = None,
        cover_ids: Optional[List[int]] = None,
        audio_ids: Optional[List[int]] = None,
        topic_ids: Optional[List[int]] = None,
        profile_id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> List[Task]:
        if not video_ids or not account_ids:
            return []

        assembler = TaskAssembler(self.db)
        tasks: List[Task] = []

        for acct_id in account_ids:
            task = await assembler.assemble(
                account_id=acct_id,
                video_ids=video_ids,
                copywriting_ids=copywriting_ids,
                cover_ids=cover_ids,
                audio_ids=audio_ids,
                topic_ids=topic_ids,
                profile_id=profile_id,
                name=name,
            )
            tasks.append(task)

        logger.info(
            "TaskDistributor: 账号数={}, 任务数={}",
            len(account_ids), len(tasks),
        )
        return tasks
