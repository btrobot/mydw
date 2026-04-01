"""
素材服务
"""
import os
import hashlib
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
from loguru import logger

from models import Material
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


# 支持的文件类型
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'}
TEXT_EXTENSIONS = {'.txt', '.md'}


class MaterialService:
    """素材服务"""

    def __init__(self, db: AsyncSession, base_path: str):
        self.db = db
        self.base_path = Path(base_path)

    def get_file_type(self, file_path: Path) -> Optional[str]:
        """根据文件扩展名判断素材类型"""
        ext = file_path.suffix.lower()

        if ext in VIDEO_EXTENSIONS:
            return "video"
        elif ext in AUDIO_EXTENSIONS:
            return "audio"
        elif ext in IMAGE_EXTENSIONS:
            return "cover"
        elif ext in TEXT_EXTENSIONS:
            # 检查文件名判断是文案还是话题
            name_lower = file_path.stem.lower()
            if "topic" in name_lower or "话题" in file_path.name:
                return "topic"
            return "text"
        return None

    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件 MD5 哈希"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.warning(f"计算文件哈希失败: {file_path}, {e}")
            return ""

    async def scan_directory(self, material_type: str = None) -> List[dict]:
        """
        扫描素材目录，返回文件列表
        """
        files = []

        if material_type:
            # 扫描指定类型目录
            type_dir = self.base_path / material_type
            if type_dir.exists():
                files.extend(await self._scan_dir(type_dir))
        else:
            # 扫描所有类型目录
            for subdir in ['video', 'text', 'cover', 'topic', 'audio']:
                type_dir = self.base_path / subdir
                if type_dir.exists():
                    type_files = await self._scan_dir(type_dir)
                    for f in type_files:
                        f['type'] = subdir
                    files.extend(type_files)

        return files

    async def _scan_dir(self, directory: Path) -> List[dict]:
        """扫描单个目录"""
        files = []
        try:
            for item in directory.iterdir():
                if item.is_file():
                    file_type = self.get_file_type(item)
                    if file_type:
                        stat = item.stat()
                        files.append({
                            'name': item.name,
                            'path': str(item),
                            'size': stat.st_size,
                            'type': file_type,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'hash': self.calculate_file_hash(item)
                        })
        except Exception as e:
            logger.error(f"扫描目录失败: {directory}, {e}")

        return files

    async def import_material(self, file_path: str) -> Optional[Material]:
        """
        导入单个素材到数据库
        返回是否成功导入
        """
        path = Path(file_path)

        if not path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return None

        # 检查是否已存在（通过路径）
        result = await self.db.execute(
            select(Material).where(Material.path == str(path))
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"素材已存在: {file_path}")
            return existing

        # 判断类型
        material_type = self.get_file_type(path)
        if not material_type:
            logger.warning(f"不支持的文件类型: {file_path}")
            return None

        # 读取文本内容（如果是文本文件）
        content = None
        if material_type in ['text', 'topic']:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                try:
                    with open(path, 'r', encoding='gbk') as f:
                        content = f.read()
                except Exception as e:
                    logger.warning(f"读取文本文件失败: {file_path}, {e}")

        # 创建素材记录
        stat = path.stat()
        material = Material(
            type=material_type,
            name=path.name,
            path=str(path),
            content=content,
            size=stat.st_size
        )

        self.db.add(material)
        await self.db.commit()
        await self.db.refresh(material)

        logger.info(f"导入素材: {path.name} ({material_type})")
        return material

    async def import_directory(self, material_type: str = None) -> Tuple[int, int]:
        """
        批量导入素材目录
        返回: (成功数, 失败数)
        """
        success = 0
        failed = 0

        files = await self.scan_directory(material_type)

        for file_info in files:
            try:
                material = await self.import_material(file_info['path'])
                if material:
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"导入失败: {file_info['path']}, {e}")
                failed += 1

        logger.info(f"批量导入完成: 成功 {success}, 失败 {failed}")
        return success, failed

    async def get_stats(self) -> dict:
        """获取素材统计"""
        result = await self.db.execute(
            select(
                Material.type,
                func.count(Material.id).label('count'),
                func.sum(Material.size).label('total_size')
            ).group_by(Material.type)
        )

        stats = {}
        total_count = 0
        total_size = 0

        for row in result:
            stats[row.type] = {
                'count': row.count,
                'size': row.total_size or 0
            }
            total_count += row.count
            total_size += row.total_size or 0

        stats['_total'] = {
            'count': total_count,
            'size': total_size
        }

        return stats

    async def validate_material(self, material: Material) -> bool:
        """验证素材是否有效（文件存在且可访问）"""
        if not material.path:
            return False

        path = Path(material.path)
        return path.exists() and path.is_file()
