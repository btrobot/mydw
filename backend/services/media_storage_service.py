"""
得物掘金工具 - 内容寻址媒体存储服务
"""
import asyncio
import shutil
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import httpx
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_dependencies import require_active_service_session
from models import Audio, Cover, Video
from schemas.auth import LocalAuthSessionSummary

# ============ 类型别名 ============

MediaType = Literal["videos", "covers", "audios"]

# ============ HTTP 请求头（与 product_parse_service 保持一致）============

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}

# ============ 媒体类型 → 模型映射 ============

_MODEL_MAP: dict[str, type] = {
    "videos": Video,
    "covers": Cover,
    "audios": Audio,
}


class MediaStorageService:
    """内容寻址媒体文件存储，支持基于 SHA-256 的去重和引用计数删除。"""

    BASE_DIR = "data/materials"

    def __init__(
        self,
        db: AsyncSession | None = None,
        auth_summary: LocalAuthSessionSummary | None = None,
    ) -> None:
        self.db = db
        self._auth_summary = auth_summary

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    async def store_from_url(
        self, url: str, media_type: MediaType
    ) -> tuple[str, str, int]:
        """
        下载 URL 到内容寻址存储，返回 (file_path, file_hash, file_size)。
        若目标目录已存在同 hash 文件则跳过下载，直接返回已有路径。
        """
        await self._require_active()
        ext = self._ext_from_url(url)
        tmp_path: str | None = None

        try:
            tmp_path = await self._download_to_temp(url)
            file_hash = await asyncio.to_thread(self._hash_file, tmp_path)
            target = self._target_path(file_hash, ext, media_type)

            if await asyncio.to_thread(os.path.exists, target):
                file_size = await asyncio.to_thread(os.path.getsize, target)
                logger.info(
                    "媒体文件已存在，跳过下载: hash={}, path={}",
                    file_hash[:16],
                    target,
                )
                return target, file_hash, file_size

            await asyncio.to_thread(self._ensure_dir, target)
            await asyncio.to_thread(shutil.move, tmp_path, target)
            tmp_path = None  # rename 成功，不再需要清理

            file_size = await asyncio.to_thread(os.path.getsize, target)
            logger.info(
                "媒体文件存储完成: media_type={}, hash={}, size={}",
                media_type,
                file_hash[:16],
                file_size,
            )
            return target, file_hash, file_size

        except (httpx.HTTPStatusError, httpx.RequestError):
            raise
        except Exception as e:
            logger.error(
                "store_from_url 失败: media_type={}, error_type={}",
                media_type,
                type(e).__name__,
            )
            raise
        finally:
            if tmp_path and await asyncio.to_thread(os.path.exists, tmp_path):
                await asyncio.to_thread(os.unlink, tmp_path)

    async def store_from_path(
        self, source_path: str, media_type: MediaType
    ) -> tuple[str, str, int]:
        """
        将本地文件存入内容寻址存储，返回 (file_path, file_hash, file_size)。
        若目标已存在则跳过复制，直接返回已有路径。
        """
        await self._require_active()
        ext = Path(source_path).suffix.lower() or ".bin"
        file_hash = await asyncio.to_thread(self._hash_file, source_path)
        target = self._target_path(file_hash, ext, media_type)

        if await asyncio.to_thread(os.path.exists, target):
            file_size = await asyncio.to_thread(os.path.getsize, target)
            logger.info(
                "媒体文件已存在，跳过复制: hash={}, path={}",
                file_hash[:16],
                target,
            )
            return target, file_hash, file_size

        await asyncio.to_thread(self._ensure_dir, target)

        await asyncio.to_thread(shutil.copy2, source_path, target)

        file_size = await asyncio.to_thread(os.path.getsize, target)
        logger.info(
            "本地文件存储完成: media_type={}, hash={}, size={}",
            media_type,
            file_hash[:16],
            file_size,
        )
        return target, file_hash, file_size

    async def safe_delete_async(
        self,
        file_path: str,
        file_hash: str,
        media_type: MediaType,
        db: AsyncSession,
    ) -> bool:
        """
        异步版本：查询 DB 引用计数，无引用才删除物理文件。
        返回 True 表示文件已删除，False 表示仍有引用或文件不存在。
        """
        await self._require_active(db)
        ref_count = await self._count_hash_refs(db, file_hash)
        if ref_count > 0:
            logger.info(
                "文件仍有 {} 条引用，跳过删除: hash={}", ref_count, file_hash[:16]
            )
            return False

        if not await asyncio.to_thread(os.path.exists, file_path):
            logger.warning("safe_delete_async: 文件不存在: path={}", file_path)
            return False

        try:
            await asyncio.to_thread(os.unlink, file_path)
            logger.info(
                "物理文件已删除: media_type={}, hash={}", media_type, file_hash[:16]
            )
            return True
        except OSError as e:
            logger.error(
                "物理文件删除失败: path={}, error_type={}", file_path, type(e).__name__
            )
            return False

    # ------------------------------------------------------------------
    # 私有辅助方法
    # ------------------------------------------------------------------

    async def _require_active(self, db: AsyncSession | None = None) -> None:
        resolved_db = db or self.db
        if resolved_db is None:
            raise ValueError("MediaStorageService auth enforcement requires an AsyncSession")
        await require_active_service_session(
            resolved_db,
            auth_summary=self._auth_summary,
        )

    def _hash_file(self, path: str) -> str:
        """计算文件 SHA-256，返回 64 位十六进制字符串。"""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _target_path(self, file_hash: str, ext: str, media_type: str) -> str:
        """生成目标路径: data/materials/{media_type}/{hash[:16]}{ext}"""
        filename = f"{file_hash[:16]}{ext}"
        return str(Path(self.BASE_DIR) / media_type / filename)

    async def _download_to_temp(self, url: str) -> str:
        """流式下载 URL 到临时文件，返回临时文件路径。"""
        suffix = Path(urlparse(url).path).suffix or ".tmp"
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(tmp_fd)

        logger.info("开始流式下载: url_prefix={}", url[:60])

        async with httpx.AsyncClient(
            headers=_HEADERS, timeout=60.0, follow_redirects=True
        ) as client:
            try:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    with open(tmp_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
            except httpx.HTTPStatusError as e:
                logger.warning(
                    "下载失败: status={}", e.response.status_code
                )
                raise
            except httpx.RequestError as e:
                logger.error("下载网络错误: error_type={}", type(e).__name__)
                raise

        return tmp_path

    @staticmethod
    def _ext_from_url(url: str) -> str:
        """从 URL 路径提取扩展名，无法识别时返回 .bin。"""
        path = urlparse(url).path
        ext = Path(path).suffix.lower()
        return ext if ext else ".bin"

    @staticmethod
    def _ensure_dir(file_path: str) -> None:
        """确保文件所在目录存在。"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    async def _count_hash_refs(self, db: AsyncSession, file_hash: str) -> int:
        """统计所有媒体表中引用该 hash 的记录总数。"""
        total = 0
        for model in (Video, Cover, Audio):
            if not hasattr(model, "file_hash"):
                continue
            result = await db.execute(
                select(func.count())
                .select_from(model)
                .where(model.file_hash == file_hash)
            )
            total += result.scalar() or 0
        return total
