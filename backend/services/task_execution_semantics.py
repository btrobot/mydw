"""
任务执行语义解析

Phase 2 / PR2:
- 定义当前版本 direct publish 的保守 Route A 规则
- 在 publish path 中显式拒绝非法任务，避免静默取第一项
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from models import Task
from utils.local_ffmpeg_contract import validate_local_ffmpeg_task_inputs


class TaskSemanticsError(ValueError):
    """任务资源组合不满足当前语义。"""


class PublishabilityError(ValueError):
    """任务不满足当前 direct publish 语义。"""


@dataclass(frozen=True)
class PublishExecutionView:
    """当前版本 direct publish 可执行视图。"""

    video_path: str
    content: str
    cover_path: Optional[str]
    topic: Optional[str]


def validate_task_resource_inputs(
    *,
    video_ids: list[int],
    copywriting_ids: Optional[list[int]] = None,
    cover_ids: Optional[list[int]] = None,
    audio_ids: Optional[list[int]] = None,
    composition_mode: Optional[str] = None,
) -> None:
    """
    校验创建/组装时的任务资源组合。

    Route A:
    - direct publish (`composition_mode` 为空或 `none`)：
      - 必须且仅能有 1 个最终视频
      - 允许 0/1 个文案
      - 允许 0/1 个封面
      - 不允许独立音频输入
    - composition 模式：
      - 允许 broader inputs，后续由合成流程处理
    """
    mode = composition_mode or "none"
    copywritings = copywriting_ids or []
    covers = cover_ids or []
    audios = audio_ids or []

    if mode == "coze":
        return

    if mode == "local_ffmpeg":
        try:
            validate_local_ffmpeg_task_inputs(
                video_ids=video_ids,
                copywriting_ids=copywritings,
                cover_ids=covers,
                audio_ids=audios,
            )
        except ValueError as exc:
            raise TaskSemanticsError(str(exc)) from exc
        return

    if mode != "none":
        raise TaskSemanticsError(f"不支持的 composition_mode: {mode}")

    if len(video_ids) != 1:
        raise TaskSemanticsError(
            f"直接发布仅支持 1 个最终视频，当前请求包含 {len(video_ids)} 个视频"
        )

    if len(copywritings) > 1:
        raise TaskSemanticsError(
            f"直接发布仅支持 0 或 1 个文案，当前请求包含 {len(copywritings)} 个文案"
        )

    if len(covers) > 1:
        raise TaskSemanticsError(
            f"直接发布仅支持 0 或 1 个封面，当前请求包含 {len(covers)} 个封面"
        )

    if audios:
        raise TaskSemanticsError("直接发布不支持独立音频输入，请先走合成流程")


def resolve_publish_execution_view(task: Task) -> PublishExecutionView:
    """
    解析任务的 direct publish 可执行视图。

    当前版本（Route A）规则：
    - 允许 1 个最终视频
    - 允许 0/1 个文案
    - 允许 0/1 个封面
    - 允许多话题
    - 不允许 direct publish 静默消费多视频 / 多文案 / 多封面
    - `final_video_path` 存在时，视为合成后的最终视频，可忽略 source videos / audios
    """
    copywritings = list(task.copywritings or [])
    covers = list(task.covers or [])
    topics = list(task.topics or [])
    videos = list(task.videos or [])
    audios = list(task.audios or [])

    if len(copywritings) > 1:
        raise PublishabilityError(
            f"直接发布仅支持 0 或 1 个文案，当前任务包含 {len(copywritings)} 个文案"
        )

    if len(covers) > 1:
        raise PublishabilityError(
            f"直接发布仅支持 0 或 1 个封面，当前任务包含 {len(covers)} 个封面"
        )

    if task.final_video_path:
        video_path = task.final_video_path
    else:
        if len(videos) != 1:
            raise PublishabilityError(
                f"直接发布仅支持 1 个最终视频，当前任务包含 {len(videos)} 个视频"
            )
        if audios:
            raise PublishabilityError("直接发布不支持独立音频输入，请先走合成流程")
        video_path = videos[0].file_path

    if not video_path:
        raise PublishabilityError("任务缺少可发布视频")

    return PublishExecutionView(
        video_path=video_path,
        content=copywritings[0].content if copywritings else "",
        cover_path=covers[0].file_path if covers else None,
        topic=", ".join(topic.name for topic in topics) if topics else None,
    )
