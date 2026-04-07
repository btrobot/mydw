"""
视频元数据提取工具 (SP7-01)

使用 FFprobe 提取视频的 duration, width, height, file_size。
FFprobe 不可用时 graceful fallback。
"""
import asyncio
import json
import shutil
from pathlib import Path
from typing import Optional

from loguru import logger
from pydantic import BaseModel


class VideoMetadata(BaseModel):
    """视频元数据"""
    duration: Optional[int] = None  # 秒
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None


def _ffprobe_available() -> bool:
    return shutil.which("ffprobe") is not None


async def extract_video_metadata(file_path: str) -> VideoMetadata:
    """提取视频元数据，FFprobe 不可用时仅返回 file_size。"""
    meta = VideoMetadata()

    # file_size 始终可获取
    p = Path(file_path)
    if p.exists():
        meta.file_size = p.stat().st_size

    if not _ffprobe_available():
        logger.warning("ffprobe 不可用，跳过元数据提取: file={}", file_path)
        return meta

    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)

        data = json.loads(stdout.decode())

        # duration from format
        fmt = data.get("format", {})
        if "duration" in fmt:
            meta.duration = int(float(fmt["duration"]))

        # width/height from first video stream
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                meta.width = stream.get("width")
                meta.height = stream.get("height")
                if meta.duration is None and "duration" in stream:
                    meta.duration = int(float(stream["duration"]))
                break

    except asyncio.TimeoutError:
        logger.warning("ffprobe 超时: file={}", file_path)
    except Exception as e:
        logger.warning("ffprobe 提取失败: file={}, error={}", file_path, str(e))

    return meta
