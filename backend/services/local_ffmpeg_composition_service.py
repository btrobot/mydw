"""
Local FFmpeg composition runner for the frozen V1 task contract.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from utils.local_ffmpeg_contract import DEFAULT_LOCAL_FFMPEG_PARAMS, parse_local_ffmpeg_params


@dataclass(frozen=True)
class LocalFFmpegCompositionResult:
    """Normalized result returned by the local FFmpeg execution path."""

    output_video_path: str
    output_video_duration: int | None = None
    output_video_size: int | None = None


class LocalFFmpegCompositionService:
    """Execute the minimal local_ffmpeg V1 composition flow."""

    def __init__(
        self,
        *,
        ffmpeg_path: str = "ffmpeg",
        ffprobe_path: str = "ffprobe",
        output_dir: str | Path = "data/videos",
    ) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.output_dir = Path(output_dir)

    async def compose(
        self,
        *,
        task_id: int,
        source_video_path: str,
        audio_path: str | None = None,
        raw_params: str | None = None,
    ) -> LocalFFmpegCompositionResult:
        """Compose a final video locally via FFmpeg."""
        params = {
            **DEFAULT_LOCAL_FFMPEG_PARAMS,
            **parse_local_ffmpeg_params(raw_params),
        }
        output_path = self.output_dir / f"final_{task_id}.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        source_has_audio = await self._video_has_audio(source_video_path)
        command = self._build_ffmpeg_command(
            source_video_path=source_video_path,
            audio_path=audio_path,
            output_path=output_path,
            source_has_audio=source_has_audio,
            params=params,
        )
        await self._run_command(command, tool_name="ffmpeg")

        if not output_path.exists():
            raise RuntimeError("local_ffmpeg 未生成输出文件")

        output_video_duration, output_video_size = await self._probe_output(output_path)
        logger.info(
            "local_ffmpeg composition completed: task_id={}, output_path={}",
            task_id,
            output_path,
        )
        return LocalFFmpegCompositionResult(
            output_video_path=str(output_path),
            output_video_duration=output_video_duration,
            output_video_size=output_video_size,
        )

    def _build_ffmpeg_command(
        self,
        *,
        source_video_path: str,
        audio_path: str | None,
        output_path: Path,
        source_has_audio: bool,
        params: dict,
    ) -> list[str]:
        params = {
            **DEFAULT_LOCAL_FFMPEG_PARAMS,
            **params,
        }
        video_codec = str(params["video_codec"])
        audio_codec = str(params["audio_codec"])
        preset = str(params["preset"])
        crf = int(params["crf"])
        audio_mix_volume = float(params["audio_mix_volume"])

        command = [
            self.ffmpeg_path,
            "-y",
            "-i",
            source_video_path,
        ]

        if audio_path:
            command.extend(["-i", audio_path])
            if source_has_audio:
                command.extend(
                    [
                        "-filter_complex",
                        (
                            "[0:a]volume=1[a0];"
                            f"[1:a]volume={audio_mix_volume}[a1];"
                            "[a0][a1]amix=inputs=2:duration=first:dropout_transition=2[aout]"
                        ),
                        "-map",
                        "0:v:0",
                        "-map",
                        "[aout]",
                    ]
                )
            else:
                command.extend(["-map", "0:v:0", "-map", "1:a:0"])
            command.append("-shortest")
        else:
            command.extend(["-map", "0:v:0", "-map", "0:a?"])

        command.extend(
            [
                "-c:v",
                video_codec,
                "-preset",
                preset,
                "-crf",
                str(crf),
                "-c:a",
                audio_codec,
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )
        return command

    async def _video_has_audio(self, video_path: str) -> bool:
        data = await self._probe_json(
            [
                "-show_streams",
                "-select_streams",
                "a",
                video_path,
            ]
        )
        streams = data.get("streams", [])
        return any(stream.get("codec_type") == "audio" for stream in streams)

    async def _probe_output(self, output_path: Path) -> tuple[int | None, int | None]:
        data = await self._probe_json(["-show_format", str(output_path)])
        format_info = data.get("format", {})

        duration_raw = format_info.get("duration")
        size_raw = format_info.get("size")

        duration = None
        if duration_raw not in (None, ""):
            duration = int(round(float(duration_raw)))

        size = None
        if size_raw not in (None, ""):
            size = int(size_raw)
        elif output_path.exists():
            size = output_path.stat().st_size

        return duration, size

    async def _probe_json(self, args: list[str]) -> dict:
        stdout = await self._run_command(
            [
                self.ffprobe_path,
                "-v",
                "quiet",
                "-print_format",
                "json",
                *args,
            ],
            tool_name="ffprobe",
        )
        try:
            return json.loads(stdout or "{}")
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
            raise RuntimeError("ffprobe 输出不是合法 JSON") from exc

    async def _run_command(self, command: list[str], *, tool_name: str) -> str:
        logger.debug("{} command: {}", tool_name, " ".join(command))
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"未找到 {tool_name} 可执行文件，请确认已安装并位于 PATH 中"
            ) from exc

        stdout, stderr = await process.communicate()
        stdout_text = stdout.decode("utf-8", errors="ignore")
        stderr_text = stderr.decode("utf-8", errors="ignore")

        if process.returncode != 0:
            detail = (
                stderr_text.strip().splitlines()[-1]
                if stderr_text.strip()
                else stdout_text.strip().splitlines()[-1]
                if stdout_text.strip()
                else "未知错误"
            )
            raise RuntimeError(f"{tool_name} 执行失败: {detail}")

        return stdout_text
