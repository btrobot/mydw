"""
得物掘金工具 - 数据库初始化
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func, UniqueConstraint
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
    status = Column(String(32), default="active", index=True)  # active, inactive, error, session_expired, disabled
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 扩展字段（账号管理 P0 — 001_account_management）
    phone_encrypted = Column(Text, nullable=True)            # AES-256-GCM 加密手机号
    dewu_nickname = Column(String(128), nullable=True)       # 得物昵称
    dewu_uid = Column(String(64), nullable=True)             # 得物平台 UID
    avatar_url = Column(String(512), nullable=True)          # 头像 URL
    tags = Column(Text, default='[]')                        # JSON 数组标签
    remark = Column(Text, nullable=True)                     # 备注
    session_expires_at = Column(DateTime, nullable=True)     # Session 过期时间
    last_health_check = Column(DateTime, nullable=True)      # 上次健康检查时间
    login_fail_count = Column(Integer, default=0)            # 连续登录失败次数

    # 关系
    tasks = relationship("Task", back_populates="account")


class Task(Base):
    """任务表"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)

    # 素材 FK
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True, index=True)
    copywriting_id = Column(Integer, ForeignKey("copywritings.id"), nullable=True, index=True)
    audio_id = Column(Integer, ForeignKey("audios.id"), nullable=True, index=True)
    cover_id = Column(Integer, ForeignKey("covers.id"), nullable=True, index=True)

    status = Column(String(32), default="pending", index=True)  # pending, running, success, failed, paused
    publish_time = Column(DateTime, nullable=True, index=True)
    error_msg = Column(Text, nullable=True)

    priority = Column(Integer, default=0)  # 优先级，数字越大优先级越高

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    account = relationship("Account", back_populates="tasks")
    product = relationship("Product", back_populates="tasks")
    logs = relationship("PublishLog", back_populates="task")
    video = relationship("Video")
    copywriting = relationship("Copywriting")
    audio = relationship("Audio")
    cover = relationship("Cover")
    topics = relationship("Topic", secondary="task_topics", passive_deletes=True)



class Product(Base):
    """商品表"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), unique=True, nullable=False, index=True)
    link = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    dewu_url = Column(String(512), nullable=True)   # 得物商品页 URL (SP1-06)
    image_url = Column(String(512), nullable=True)  # 商品图片 (SP1-06)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    tasks = relationship("Task", back_populates="product")
    videos = relationship("Video", back_populates="product")
    copywritings = relationship("Copywriting", back_populates="product")
    topics = relationship("Topic", secondary="product_topics")


class Video(Base):
    """视频素材表 (SP1-01)"""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    name = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)   # 秒
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)
    source_type = Column(String(32), default="original")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    product = relationship("Product", back_populates="videos")
    covers = relationship("Cover", back_populates="video")


class Copywriting(Base):
    """文案素材表 (SP1-02)"""
    __tablename__ = "copywritings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    source_type = Column(String(32), default="manual")
    source_ref = Column(String(256), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    product = relationship("Product", back_populates="copywritings")


class Cover(Base):
    """封面素材表 (SP1-03)"""
    __tablename__ = "covers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True, index=True)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    video = relationship("Video", back_populates="covers")


class Audio(Base):
    """音频素材表 (SP1-04)"""
    __tablename__ = "audios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)  # 秒

    created_at = Column(DateTime, default=datetime.utcnow)


class Topic(Base):
    """话题表 (SP1-05)"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), unique=True, nullable=False, index=True)
    heat = Column(Integer, default=0)
    source = Column(String(32), default="manual")
    last_synced = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class TaskTopic(Base):
    """任务-话题关联表 (SP3-02)"""
    __tablename__ = "task_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint('task_id', 'topic_id'),)


class ProductTopic(Base):
    """商品-话题关联表"""
    __tablename__ = "product_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint('product_id', 'topic_id'),)


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
    global_topic_ids = Column(Text, default='[]')  # JSON数组存储全局话题ID

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

    # 执行迁移脚本（幂等）
    import importlib
    migration_001 = importlib.import_module("migrations.001_account_management")
    await migration_001.run_migration(engine)
    migration_002 = importlib.import_module("migrations.002_material_product_link")
    await migration_002.run_migration(engine)
    migration_003 = importlib.import_module("migrations.003_product_enhance")
    await migration_003.run_migration(engine)
    migration_004 = importlib.import_module("migrations.004_material_split")
    await migration_004.run_migration(engine)
    migration_005 = importlib.import_module("migrations.005_task_add_fk")
    await migration_005.run_migration(engine)
    migration_006 = importlib.import_module("migrations.006_global_topics")
    await migration_006.run_migration(engine)
    migration_007 = importlib.import_module("migrations.007_task_topic_unique")
    await migration_007.run_migration(engine)
    migration_008 = importlib.import_module("migrations.008_task_cover_fk")
    await migration_008.run_migration(engine)
    migration_009 = importlib.import_module("migrations.009_product_topics")
    await migration_009.run_migration(engine)

    logger.info("数据库初始化完成")


async def get_db():
    """获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
