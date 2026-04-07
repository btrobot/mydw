"""
文件哈希工具 (SP8-01)
"""
import asyncio
import hashlib
from pathlib import Path
from typing import Optional

from loguru import logger


def _compute_hash_sync(file_path: str, algorithm: str) -> str:
    """同步计算文件哈希（在线程池中执行，避免阻塞事件循环）。"""
    h = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


async def compute_file_hash(file_path: str, algorithm: str = "sha256") -> Optional[str]:
    """计算文件 SHA-256 哈希，文件不存在或出错返回 None。"""
    p = Path(file_path)
    if not p.exists():
        return None
    try:
        return await asyncio.to_thread(_compute_hash_sync, file_path, algorithm)
    except Exception as e:
        logger.warning("文件哈希计算失败: file={}, error={}", file_path, str(e))
        return None
