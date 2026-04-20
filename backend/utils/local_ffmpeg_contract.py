"""
local_ffmpeg V1 contract helpers.
"""
from __future__ import annotations

import json
from typing import Any


LOCAL_FFMPEG_ALLOWED_PARAM_KEYS = {
    "audio_mix_volume",
    "video_codec",
    "audio_codec",
    "preset",
    "crf",
}

DEFAULT_LOCAL_FFMPEG_PARAMS = {
    "audio_mix_volume": 0.3,
    "video_codec": "libx264",
    "audio_codec": "aac",
    "preset": "medium",
    "crf": 23,
}

DEFAULT_LOCAL_FFMPEG_PARAMS_JSON = json.dumps(
    DEFAULT_LOCAL_FFMPEG_PARAMS,
    ensure_ascii=False,
    separators=(",", ":"),
)


def parse_local_ffmpeg_params(raw_params: str | None) -> dict[str, Any]:
    """Parse local_ffmpeg params into a validated JSON object."""
    if raw_params in (None, ""):
        return {}

    try:
        parsed = json.loads(raw_params)
    except (TypeError, ValueError) as exc:  # pragma: no cover
        raise ValueError("composition_params 必须是合法的 JSON 字符串") from exc

    if not isinstance(parsed, dict):
        raise ValueError("local_ffmpeg 的 composition_params 必须是 JSON object")

    unknown_keys = sorted(set(parsed) - LOCAL_FFMPEG_ALLOWED_PARAM_KEYS)
    if unknown_keys:
        raise ValueError(
            "local_ffmpeg 的 composition_params 仅支持以下字段："
            f"{', '.join(sorted(LOCAL_FFMPEG_ALLOWED_PARAM_KEYS))}；"
            f"收到未知字段：{', '.join(unknown_keys)}"
        )

    audio_mix_volume = parsed.get("audio_mix_volume")
    if isinstance(audio_mix_volume, bool) or (
        audio_mix_volume is not None and not isinstance(audio_mix_volume, (int, float))
    ):
        raise ValueError("local_ffmpeg.audio_mix_volume 必须是数字")
    if audio_mix_volume is not None and not (0 <= float(audio_mix_volume) <= 2):
        raise ValueError("local_ffmpeg.audio_mix_volume 必须位于 0 到 2 之间")

    for key in ("video_codec", "audio_codec", "preset"):
        value = parsed.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"local_ffmpeg.{key} 必须是非空字符串")

    crf = parsed.get("crf")
    if crf is not None:
        if isinstance(crf, bool) or not isinstance(crf, int):
            raise ValueError("local_ffmpeg.crf 必须是整数")
        if not (0 <= crf <= 51):
            raise ValueError("local_ffmpeg.crf 必须位于 0 到 51 之间")

    return parsed


def validate_publish_profile_contract(
    *,
    composition_mode: str,
    composition_params: str | None,
    coze_workflow_id: str | None,
) -> None:
    """Validate mode-specific profile contract before persistence."""
    mode = composition_mode or "none"

    if mode == "local_ffmpeg":
        if coze_workflow_id:
            raise ValueError("local_ffmpeg 模式不允许填写 coze_workflow_id")
        parse_local_ffmpeg_params(composition_params)
        return

    if mode in {"coze", "none"}:
        return

    raise ValueError(f"不支持的 composition_mode: {mode}")


def validate_local_ffmpeg_task_inputs(
    *,
    video_ids: list[int],
    copywriting_ids: list[int] | None = None,
    cover_ids: list[int] | None = None,
    audio_ids: list[int] | None = None,
) -> None:
    """Validate the frozen V1 task input contract for local_ffmpeg."""
    copywritings = copywriting_ids or []
    covers = cover_ids or []
    audios = audio_ids or []

    if len(video_ids) != 1:
        raise ValueError(f"local_ffmpeg V1 仅支持 1 个视频输入，当前请求包含 {len(video_ids)} 个视频")

    if len(audios) > 1:
        raise ValueError(f"local_ffmpeg V1 仅支持 0 或 1 个音频输入，当前请求包含 {len(audios)} 个音频")

    if len(copywritings) > 1:
        raise ValueError(
            f"local_ffmpeg V1 仅支持 0 或 1 个文案输入（文案保留给发布层），当前请求包含 {len(copywritings)} 个文案"
        )

    if len(covers) > 1:
        raise ValueError(
            f"local_ffmpeg V1 仅支持 0 或 1 个封面输入（封面保留给发布层），当前请求包含 {len(covers)} 个封面"
        )
