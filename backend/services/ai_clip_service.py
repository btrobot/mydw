"""
AI 剪辑服务
"""
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from datetime import datetime
from dataclasses import dataclass
from loguru import logger

import httpx

from core.config import settings


@dataclass
class VideoInfo:
    """视频信息"""
    path: str
    duration: float  # 秒
    width: int
    height: int
    fps: float
    size: int  # bytes
    format: str


@dataclass
class ClipSegment:
    """剪辑片段"""
    start: float  # 秒
    end: float
    reason: str = ""


@dataclass
class ClipResult:
    """剪辑结果"""
    success: bool
    output_path: Optional[str] = None
    duration: float = 0
    error: Optional[str] = None


class AIClipService:
    """AI 剪辑服务"""

    def __init__(self):
        self.ffmpeg_path = "ffmpeg"  # 使用系统 FFmpeg
        self.ffprobe_path = "ffprobe"

    async def get_video_info(self, video_path: str) -> Optional[VideoInfo]:
        """获取视频信息"""
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                logger.error(f"获取视频信息失败: {stderr.decode()}")
                return None

            data = json.loads(stdout.decode())

            # 查找视频流
            video_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break

            if not video_stream:
                return None

            duration = float(data.get("format", {}).get("duration", 0))
            size = int(data.get("format", {}).get("size", 0))

            return VideoInfo(
                path=video_path,
                duration=duration,
                width=int(video_stream.get("width", 0)),
                height=int(video_stream.get("height", 0)),
                fps=eval(video_stream.get("r_frame_rate", "0/1")),
                size=size,
                format=video_stream.get("codec_name", "unknown")
            )

        except Exception as e:
            logger.error(f"获取视频信息异常: {e}")
            return None

    async def detect_highlights(self, video_path: str) -> List[ClipSegment]:
        """
        检测视频高光片段（简化版）
        实际项目中可以使用 OpenCV 或 AI 模型分析
        """
        try:
            video_info = await self.get_video_info(video_path)
            if not video_info:
                return []

            duration = video_info.duration

            # 简化策略：将视频平均分成 3-5 段
            # 实际项目中这里应该使用 AI 模型分析
            num_segments = min(5, max(3, int(duration / 30)))

            segments = []
            segment_duration = duration / num_segments

            for i in range(num_segments):
                start = i * segment_duration
                end = (i + 1) * segment_duration
                # 保留每段的前 80%
                segments.append(ClipSegment(
                    start=start,
                    end=start + segment_duration * 0.8,
                    reason=f"高光片段 {i+1}"
                ))

            logger.info(f"检测到 {len(segments)} 个高光片段")
            return segments

        except Exception as e:
            logger.error(f"检测高光失败: {e}")
            return []

    async def smart_clip(
        self,
        video_path: str,
        segments: List[ClipSegment],
        output_path: str,
        target_duration: int = 60
    ) -> ClipResult:
        """
        智能剪辑视频
        """
        try:
            if not segments:
                return ClipResult(success=False, error="没有剪辑片段")

            # 构建 FFmpeg 滤镜
            # 使用 concat 滤镜合并多个片段
            filter_parts = []
            for i, seg in enumerate(segments):
                filter_parts.append(
                    f"[0:v]trim=start={seg.start}:end={seg.end},setpts=PTS-STARTPTS[v{i}];"
                    f"[0:a]atrim=start={seg.start}:end={seg.end},asetpts=PTS-STARTPTS[a{i}]"
                )

            # 构建 concat 输入
            concat_inputs = ""
            concat_filter = ""
            for i in range(len(segments)):
                concat_inputs += f"[v{i}][a{i}]"
                concat_filter += f"[{i}:v][{i}:a]"

            filter_complex = (
                ";".join(filter_parts) +
                f";{concat_inputs}concat=n={len(segments)}:v=1:a=1[outv][outa]"
            )

            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-map", "[outa]",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-y",  # 覆盖输出文件
                output_path
            ]

            logger.info(f"开始剪辑视频: {video_path}")
            logger.debug(f"FFmpeg 命令: {' '.join(cmd)}")

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode()[-500:] if stderr else "未知错误"
                logger.error(f"FFmpeg 执行失败: {error_msg}")
                return ClipResult(success=False, error=error_msg)

            # 检查输出文件
            output = Path(output_path)
            if not output.exists():
                return ClipResult(success=False, error="输出文件未生成")

            # 获取输出视频时长
            output_info = await self.get_video_info(output_path)

            logger.info(f"视频剪辑完成: {output_path}")
            return ClipResult(
                success=True,
                output_path=output_path,
                duration=output_info.duration if output_info else 0
            )

        except Exception as e:
            logger.error(f"剪辑异常: {e}")
            return ClipResult(success=False, error=str(e))

    async def add_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        volume: float = 0.3
    ) -> ClipResult:
        """添加背景音乐"""
        try:
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-i", audio_path,
                "-filter_complex",
                f"[1:a]volume={volume}[a1];[0:a][a1]amix=inputs=2:duration=first[aout]",
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-y",
                output_path
            ]

            logger.info(f"添加背景音乐: {audio_path}")

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode()[-500:] if stderr else "未知错误"
                return ClipResult(success=False, error=error_msg)

            return ClipResult(success=True, output_path=output_path)

        except Exception as e:
            return ClipResult(success=False, error=str(e))

    async def add_cover(
        self,
        video_path: str,
        cover_path: str,
        output_path: str
    ) -> ClipResult:
        """添加封面"""
        try:
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-i", cover_path,
                "-map", "0:v",
                "-map", "1:v",
                "-c:v", "copy",
                "-y",
                output_path
            ]

            logger.info(f"添加封面: {cover_path}")

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode()[-500:] if stderr else "未知错误"
                return ClipResult(success=False, error=error_msg)

            return ClipResult(success=True, output_path=output_path)

        except Exception as e:
            return ClipResult(success=False, error=str(e))

    async def trim_video(
        self,
        video_path: str,
        start: float,
        end: float,
        output_path: str
    ) -> ClipResult:
        """截取视频片段"""
        try:
            duration = end - start

            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-ss", str(start),
                "-t", str(duration),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-y",
                output_path
            ]

            logger.info(f"截取视频: {start}s - {end}s")

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                error_msg = stderr.decode()[-500:] if stderr else "未知错误"
                return ClipResult(success=False, error=error_msg)

            return ClipResult(success=True, output_path=output_path, duration=duration)

        except Exception as e:
            return ClipResult(success=False, error=str(e))

    async def full_pipeline(
        self,
        video_path: str,
        audio_path: str = None,
        cover_path: str = None,
        target_duration: int = 60,
        output_dir: str = None
    ) -> Tuple[ClipResult, Optional[str]]:
        """
        完整剪辑流程
        1. 检测高光
        2. 智能剪辑
        3. 添加音频（可选）
        4. 添加封面（可选）
        """
        try:
            output_dir = Path(output_dir or Path(video_path).parent)
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = Path(video_path).stem

            # 步骤1: 检测高光
            logger.info("[1/4] 检测视频高光...")
            segments = await self.detect_highlights(video_path)

            if not segments:
                return ClipResult(success=False, error="未能检测到高光片段"), None

            # 步骤2: 智能剪辑
            clip_output = output_dir / f"{base_name}_clip_{timestamp}.mp4"
            logger.info("[2/4] 执行智能剪辑...")

            clip_result = await self.smart_clip(
                video_path,
                segments,
                str(clip_output),
                target_duration
            )

            if not clip_result.success:
                return clip_result, None

            current_video = clip_result.output_path

            # 步骤3: 添加音频
            if audio_path and Path(audio_path).exists():
                logger.info("[3/4] 添加背景音乐...")
                audio_output = output_dir / f"{base_name}_audio_{timestamp}.mp4"

                audio_result = await self.add_audio(
                    current_video,
                    audio_path,
                    str(audio_output)
                )

                if audio_result.success:
                    current_video = audio_result.output_path

            # 步骤4: 添加封面
            if cover_path and Path(cover_path).exists():
                logger.info("[4/4] 添加封面...")
                final_output = output_dir / f"{base_name}_final_{timestamp}.mp4"

                cover_result = await self.add_cover(
                    current_video,
                    cover_path,
                    str(final_output)
                )

                if cover_result.success:
                    current_video = cover_result.output_path

            logger.info(f"剪辑流程完成: {current_video}")
            return ClipResult(success=True, output_path=current_video), current_video

        except Exception as e:
            logger.error(f"剪辑流程异常: {e}")
            return ClipResult(success=False, error=str(e)), None


# 全局实例
ai_clip_service = AIClipService()
