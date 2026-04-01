"""
得物掘金工具 - 数据库初始化
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from loguru import logger

Base = declarative_base()


class Account(Base):
    """账号表"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String(64), unique=True, nullable=False, index=True)
    account_name = Column(String(128), nullable=False)
    cookie = Column(Text, nullable=True)  # 加密存储
    storage_state = Column(Text, nullable=True)  # Playwright storage state
    status = Column(String(32), default="active", index=True)  # active, inactive, error
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    tasks = relationship("Task", back_populates="account")


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)

    video_path = Column(String(512), nullable=True)
    content = Column(Text, nullable=True)  # 文案
    topic = Column(String(256), nullable=True)  # 话题
    cover_path = Column(String(512), nullable=True)
    audio_path = Column(String(512), nullable=True)

    status = Column(String(32), default="pending", index=True)  # pending, running, success, failed, paused
    publish_time = Column(DateTime, nullable=True, index=True)
    error_msg = Column(Text, nullable=True)

    priority = Column(Integer, default=0)  # 优先级，数字越大优先级越高

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    account = relationship("Account", back_populates="tasks")
    product = relationship("Product", back_populates="tasks")
    material = relationship("Material", back_populates="tasks")
    logs = relationship("PublishLog", back_populates="task")


class Material(Base):
    """素材表"""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(32), nullable=False, index=True)  # video, text, cover, topic, audio
    name = Column(String(256), nullable=True)
    path = Column(String(512), nullable=True)  # 文件路径
    content = Column(Text, nullable=True)  # 文本内容（文案/话题）
    size = Column(Integer, nullable=True)  # 文件大小
    duration = Column(Integer, nullable=True)  # 视频时长（秒）

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    tasks = relationship("Task", back_populates="material")


class Product(Base):
    """商品表"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), unique=True, nullable=False, index=True)
    link = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    tasks = relationship("Task", back_populates="product")


class PublishLog(Base):
    """发布日志表"""
    __tablename__ = "publish_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)

    status = Column(String(32), nullable=False)  # started, success, failed
    message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 关系
    task = relationship("Task", back_populates="logs")


class PublishConfig(Base):
    """发布配置表"""
    __tablename__ = "publish_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), default="default")
    interval_minutes = Column(Integer, default=30)
    start_hour = Column(Integer, default=9)
    end_hour = Column(Integer, default=22)
    max_per_account_per_day = Column(Integer, default=5)
    shuffle = Column(Boolean, default=False)
    auto_start = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(16), nullable=False)  # INFO, WARNING, ERROR
    module = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# 数据库会话
engine = None
async_session = None


async def init_db():
    """初始化数据库"""
    global engine, async_session

    from core.config import settings

    # 创建数据目录
    Path("data").mkdir(parents=True, exist_ok=True)

    # 创建异步引擎
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True
    )

    # 创建会话工厂
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("数据库初始化完成")


async def get_db():
    """获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
