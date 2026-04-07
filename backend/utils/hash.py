"""
文件哈希工具 (SP8-01)
"""
import hashlib
from pathlib import Path
from typing import Optional

from loguru import logger


async def compute_file_hash(file_path: str, algorithm: str = "sha256") -> Optional[str]:
    """计算文件 SHA-256 哈希，文件不存在或出错返回 None。"""
    p = Path(file_path)
    if not p.exists():
        return None
    try:
        h = hashlib.new(algorithm)
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logger.warning("文件哈希计算失败: file={}, error={}", file_path, str(e))
        return None
