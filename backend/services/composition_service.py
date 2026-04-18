"""
合成服务 (BE-TM-11)

负责 Coze 工作流合成任务的提交、状态回调和批量操作。
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.coze_client import CozeClient
from core.auth_dependencies import require_active_service_session
from models import CompositionJob, Task
from schemas.auth import LocalAuthSessionSummary
from services.creative_generation_service import CreativeGenerationService
from services.task_compat_service import resolve_primary_task_video
from services.task_service import TaskService
from utils.time import utc_now_naive


class CompositionService:
    """合成任务服务"""

    def __init__(self, db: AsyncSession, auth_summary: LocalAuthSessionSummary | None = None) -> None:
        self.db = db
        self._auth_summary = auth_summary
        self._task_service = TaskService(db, auth_summary=auth_summary)
        self._creative_generation_service = CreativeGenerationService(db)

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    async def _get_task(self, task_id: int) -> Task:
        """查询任务，不存在则抛 ValueError。"""
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = result.scalars().first()
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")
        return task

    async def _get_job(self, job_id: int) -> CompositionJob:
        """查询合成任务，不存在则抛 ValueError。"""
        result = await self.db.execute(
            select(CompositionJob).where(CompositionJob.id == job_id)
        )
        job = result.scalars().first()
        if not job:
            raise ValueError(f"合成任务 {job_id} 不存在")
        return job

    # ------------------------------------------------------------------
    # 公开方法
    # ------------------------------------------------------------------

    async def submit_composition(self, task_id: int) -> CompositionJob:
        await require_active_service_session(
            self.db,
            auth_summary=self._auth_summary,
        )
        """提交合成：上传素材 → 提交工作流 → 创建 CompositionJob → task.status=composing。

        Args:
            task_id: 任务 ID，要求当前状态为 draft。

        Returns:
            新建的 CompositionJob 实例。

        Raises:
            ValueError: 任务不存在、状态非 draft、profile 缺失或 composition_mode 不支持。
        """
        task = await self._get_task(task_id)

        if task.status != "draft":
            raise ValueError(
                f"任务 {task_id} 当前状态为 {task.status}，只有 draft 状态可提交合成"
            )

        profile = await self._task_service.resolve_profile(task)
        if not profile:
            raise ValueError(f"任务 {task_id} 未找到关联的 PublishProfile")

        composition_mode: str = profile.composition_mode or "none"
        logger.info(
            "提交合成: task_id={}, composition_mode={}", task_id, composition_mode
        )

        external_job_id: Optional[str] = None
        workflow_id: Optional[str] = None

        if composition_mode == "coze":
            workflow_id = profile.coze_workflow_id
            if not workflow_id:
                raise ValueError(
                    f"PublishProfile {profile.id} 未配置 coze_workflow_id"
                )

            # 构建工作流参数
            params: dict[str, Any] = {}
            if profile.composition_params:
                try:
                    params = json.loads(profile.composition_params)
                except json.JSONDecodeError:
                    logger.warning(
                        "profile {} composition_params JSON 解析失败，使用空参数",
                        profile.id,
                    )

            # 上传素材文件（视频）
            coze = CozeClient()
            video = await resolve_primary_task_video(self.db, task)
            if video and video.file_path:
                file_id = await coze.upload_file(video.file_path)
                params["video_file_id"] = file_id
                logger.info(
                    "素材上传完成: task_id={}, file_id={}", task_id, file_id
                )

            external_job_id = await coze.submit_composition(workflow_id, params)

        elif composition_mode == "none":
            logger.info(
                "composition_mode=none，跳过合成直接创建 job: task_id={}", task_id
            )
        else:
            raise ValueError(
                f"不支持的 composition_mode: {composition_mode}"
            )

        # 创建 CompositionJob 记录
        job = CompositionJob(
            task_id=task_id,
            workflow_type=composition_mode,
            workflow_id=workflow_id,
            external_job_id=external_job_id,
            status="pending",
            started_at=utc_now_naive(),
        )
        self.db.add(job)
        await self.db.flush()  # 获取 job.id，不提交事务

        # 更新 task
        task.composition_job_id = job.id
        task.status = "composing"
        task.updated_at = utc_now_naive()

        await self.db.commit()
        await self.db.refresh(job)

        logger.info(
            "合成任务已创建: task_id={}, job_id={}, external_job_id={}",
            task_id,
            job.id,
            external_job_id,
        )
        return job

    async def handle_success(self, job_id: int, output: dict[str, Any]) -> None:
        """合成成功回调：下载视频 → 更新 job → task.status=ready。

        Args:
            job_id: CompositionJob ID。
            output: 工作流输出字典，应包含 video_url 字段。
        """
        job = await self._get_job(job_id)
        task = await self._get_task(job.task_id)
        already_completed = job.status == "completed"

        video_url: Optional[str] = output.get("video_url")
        local_path: Optional[str] = None

        if video_url:
            dest = Path("data/videos")
            dest.mkdir(parents=True, exist_ok=True)
            local_path = str(dest / f"final_{job.task_id}.mp4")

            logger.info(
                "开始下载合成视频: job_id={}, dest={}", job_id, local_path
            )
            try:
                async with httpx.AsyncClient(timeout=300) as client:
                    async with client.stream("GET", video_url) as resp:
                        resp.raise_for_status()
                        with open(local_path, "wb") as f:
                            async for chunk in resp.aiter_bytes(chunk_size=65536):
                                f.write(chunk)
                logger.info("视频下载完成: job_id={}, path={}", job_id, local_path)
            except Exception as e:
                logger.error(
                    "视频下载失败: job_id={}, error_type={}", job_id, type(e).__name__
                )
                await self.handle_failure(job_id, f"视频下载失败: {type(e).__name__}")
                return
        else:
            logger.warning("合成输出中未包含 video_url: job_id={}", job_id)

        # 更新 CompositionJob
        job.status = "completed"
        job.progress = 100
        job.output_video_url = video_url
        job.output_video_path = local_path
        job.completed_at = utc_now_naive()
        job.updated_at = utc_now_naive()

        # 更新 Task
        task.status = "ready"
        task.final_video_path = local_path
        task.updated_at = utc_now_naive()

        if not already_completed:
            await self._creative_generation_service.record_composition_success(task)

        await self.db.commit()
        logger.info(
            "合成成功处理完毕: job_id={}, task_id={}", job_id, job.task_id
        )

    async def handle_failure(self, job_id: int, error_msg: str) -> None:
        """合成失败回调：更新 job → task.failed_at_status=composing → task.status=failed。

        Args:
            job_id: CompositionJob ID。
            error_msg: 错误描述（不含敏感信息）。
        """
        job = await self._get_job(job_id)
        task = await self._get_task(job.task_id)

        # 更新 CompositionJob
        job.status = "failed"
        job.error_msg = error_msg
        job.completed_at = utc_now_naive()
        job.updated_at = utc_now_naive()

        # 更新 Task（保留 failed_at_status 供快速重试使用）
        task.failed_at_status = "composing"
        task.status = "failed"
        task.error_msg = error_msg
        task.updated_at = utc_now_naive()

        await self._creative_generation_service.record_composition_failure(task, error_msg)

        await self.db.commit()
        logger.warning(
            "合成失败处理完毕: job_id={}, task_id={}", job_id, job.task_id
        )

    async def batch_submit(self, task_ids: list[int]) -> dict[str, Any]:
        await require_active_service_session(
            self.db,
            auth_summary=self._auth_summary,
        )
        """批量提交合成任务。

        Args:
            task_ids: 任务 ID 列表。

        Returns:
            {success_count, failed_count, results}，results 为每个 task_id 的结果列表。
        """
        success_count = 0
        failed_count = 0
        results: list[dict[str, Any]] = []

        for task_id in task_ids:
            try:
                job = await self.submit_composition(task_id)
                success_count += 1
                results.append(
                    {"task_id": task_id, "status": "submitted", "job_id": job.id}
                )
            except Exception as e:
                failed_count += 1
                results.append(
                    {
                        "task_id": task_id,
                        "status": "failed",
                        "error": str(e),
                    }
                )
                logger.warning(
                    "批量提交: task_id={} 失败, error_type={}",
                    task_id,
                    type(e).__name__,
                )

        logger.info(
            "批量提交完成: total={}, success={}, failed={}",
            len(task_ids),
            success_count,
            failed_count,
        )
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }
