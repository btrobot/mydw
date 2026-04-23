"""
得物掘金工具 - 数据库初始化
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from loguru import logger
from utils.time import utc_now_naive

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
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    # 扩展字段（账号管理 P0 — 001_account_management）
    phone_encrypted = Column(Text, nullable=True)            # AES-256-GCM 加密手机号
    dewu_nickname = Column(String(128), nullable=True)       # 得物昵称
    dewu_uid = Column(String(64), nullable=True)             # 得物平台 UID
    avatar_url = Column(String(512), nullable=True)          # 头像 URL
    tags = Column(Text, default='[]')                        # JSON 数组标签；Phase 6 最终结论为 normalize-later
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
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, index=True)

    # 旧 FK（兼容保留列，不再是 authoritative 任务语义；新逻辑应读取资源集合关系）
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True, index=True)
    copywriting_id = Column(Integer, ForeignKey("copywritings.id"), nullable=True, index=True)
    audio_id = Column(Integer, ForeignKey("audios.id"), nullable=True, index=True)
    cover_id = Column(Integer, ForeignKey("covers.id"), nullable=True, index=True)

    status = Column(String(32), default="draft", index=True)  # draft, composing, ready, uploading, uploaded, failed, cancelled
    publish_time = Column(DateTime, nullable=True, index=True)
    error_msg = Column(Text, nullable=True)

    priority = Column(Integer, default=0)  # 优先级，数字越大优先级越高

    # 合成相关字段（migration 016）
    name = Column(String(256), nullable=True)
    description = Column(String, nullable=True)
    source_video_ids = Column(String, nullable=True)          # JSON array；迁移遗留字段，Phase 6 结论为 delete-ready-later
    composition_template = Column(String(64), nullable=True)
    composition_params = Column(String, nullable=True)        # Opaque JSON params；Phase 6 结论为 keep-json
    composition_job_id = Column(Integer, nullable=True, index=True)
    final_video_path = Column(String(512), nullable=True)
    final_video_duration = Column(Integer, nullable=True)
    final_video_size = Column(Integer, nullable=True)
    scheduled_time = Column(DateTime, nullable=True, index=True)
    retry_count = Column(Integer, default=0)
    dewu_video_id = Column(String(128), nullable=True)
    dewu_video_url = Column(String(512), nullable=True)

    # 发布档案关联字段（migration 020）
    profile_id = Column(Integer, ForeignKey("publish_profiles.id"), nullable=True, index=True)
    batch_id = Column(String(64), nullable=True, index=True)
    failed_at_status = Column(String(32), nullable=True)

    # Creative Phase A ?????migration 024?
    creative_item_id = Column(Integer, ForeignKey("creative_items.id"), nullable=True, index=True)
    creative_version_id = Column(Integer, ForeignKey("creative_versions.id"), nullable=True, index=True)
    task_kind = Column(String(32), nullable=True, index=True)

    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    # 关系
    account = relationship("Account", back_populates="tasks")
    logs = relationship("PublishLog", back_populates="task")
    videos = relationship("Video", secondary="task_videos", passive_deletes=True)
    copywritings = relationship("Copywriting", secondary="task_copywritings", passive_deletes=True)
    covers = relationship("Cover", secondary="task_covers", passive_deletes=True)
    audios = relationship("Audio", secondary="task_audios", passive_deletes=True)
    topics = relationship("Topic", secondary="task_topics", passive_deletes=True)
    composition_jobs = relationship("CompositionJob", back_populates="task", order_by="CompositionJob.id")
    profile = relationship("PublishProfile", foreign_keys=[profile_id])
    creative_item = relationship("CreativeItem", back_populates="tasks", foreign_keys=[creative_item_id])
    creative_version = relationship("CreativeVersion", back_populates="tasks", foreign_keys=[creative_version_id])


class CreativeItem(Base):
    """??????Phase A ?????"""
    __tablename__ = "creative_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creative_no = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(256), nullable=True)
    status = Column(String(32), nullable=False, default="PENDING_INPUT", index=True)
    current_version_id = Column(
        Integer,
        ForeignKey("creative_versions.id", use_alter=True, name="fk_creative_items_current_version_id"),
        nullable=True,
        index=True,
    )
    latest_version_no = Column(Integer, nullable=False, default=0)
    generation_error_msg = Column(Text, nullable=True)
    generation_failed_at = Column(DateTime, nullable=True)
    subject_product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    subject_product_name_snapshot = Column(String(256), nullable=True)
    main_copywriting_text = Column(Text, nullable=True)
    target_duration_seconds = Column(Integer, nullable=True)
    input_profile_id = Column(Integer, ForeignKey("publish_profiles.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    subject_product = relationship("Product", foreign_keys=[subject_product_id])
    input_profile = relationship("PublishProfile", foreign_keys=[input_profile_id])
    input_items = relationship(
        "CreativeInputItem",
        back_populates="creative_item",
        foreign_keys="CreativeInputItem.creative_item_id",
        order_by="CreativeInputItem.sequence",
        cascade="all, delete-orphan",
    )
    current_version = relationship(
        "CreativeVersion",
        foreign_keys=[current_version_id],
        uselist=False,
        post_update=True,
    )
    versions = relationship(
        "CreativeVersion",
        back_populates="creative_item",
        foreign_keys="CreativeVersion.creative_item_id",
        order_by="CreativeVersion.version_no",
    )
    tasks = relationship("Task", back_populates="creative_item", foreign_keys="Task.creative_item_id")
    check_records = relationship(
        "CheckRecord",
        back_populates="creative_item",
        foreign_keys="CheckRecord.creative_item_id",
        order_by="CheckRecord.id",
    )
    publish_pool_items = relationship(
        "PublishPoolItem",
        back_populates="creative_item",
        foreign_keys="PublishPoolItem.creative_item_id",
        order_by="PublishPoolItem.id",
    )


class CreativeInputItem(Base):
    """Ordered, duplicate-preserving creative input composition item."""
    __tablename__ = "creative_input_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creative_item_id = Column(Integer, ForeignKey("creative_items.id"), nullable=False, index=True)
    material_type = Column(String(32), nullable=False, index=True)
    material_id = Column(Integer, nullable=False, index=True)
    role = Column(String(64), nullable=True)
    sequence = Column(Integer, nullable=False, default=0)
    instance_no = Column(Integer, nullable=False, default=1)
    trim_in = Column(Integer, nullable=True)
    trim_out = Column(Integer, nullable=True)
    slot_duration_seconds = Column(Integer, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    __table_args__ = (UniqueConstraint("creative_item_id", "sequence"),)

    creative_item = relationship(
        "CreativeItem",
        back_populates="input_items",
        foreign_keys=[creative_item_id],
    )


class CreativeVersion(Base):
    """???????Phase A ?????"""
    __tablename__ = "creative_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creative_item_id = Column(Integer, ForeignKey("creative_items.id"), nullable=False, index=True)
    parent_version_id = Column(Integer, ForeignKey("creative_versions.id"), nullable=True, index=True)
    version_no = Column(Integer, nullable=False, default=1)
    version_type = Column(String(32), nullable=False, default="generated")
    title = Column(String(256), nullable=True)
    actual_duration_seconds = Column(Integer, nullable=True)
    final_video_path = Column(String(512), nullable=True)
    final_product_name = Column(String(256), nullable=True)
    final_copywriting_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    __table_args__ = (UniqueConstraint("creative_item_id", "version_no"),)

    creative_item = relationship(
        "CreativeItem",
        back_populates="versions",
        foreign_keys=[creative_item_id],
    )
    parent_version = relationship(
        "CreativeVersion",
        remote_side=[id],
        foreign_keys=[parent_version_id],
        back_populates="child_versions",
        uselist=False,
    )
    child_versions = relationship(
        "CreativeVersion",
        back_populates="parent_version",
        foreign_keys=[parent_version_id],
        order_by="CreativeVersion.version_no",
    )
    package_records = relationship(
        "PackageRecord",
        back_populates="creative_version",
        foreign_keys="PackageRecord.creative_version_id",
    )
    check_records = relationship(
        "CheckRecord",
        back_populates="creative_version",
        foreign_keys="CheckRecord.creative_version_id",
        order_by="CheckRecord.id",
    )
    publish_pool_items = relationship(
        "PublishPoolItem",
        back_populates="creative_version",
        foreign_keys="PublishPoolItem.creative_version_id",
        order_by="PublishPoolItem.id",
    )
    tasks = relationship("Task", back_populates="creative_version", foreign_keys="Task.creative_version_id")


class PackageRecord(Base):
    """??????Phase A ?????"""
    __tablename__ = "package_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creative_version_id = Column(Integer, ForeignKey("creative_versions.id"), nullable=False, index=True)
    package_status = Column(String(32), nullable=False, default="pending", index=True)
    publish_profile_id = Column(Integer, ForeignKey("publish_profiles.id"), nullable=True, index=True)
    frozen_video_path = Column(String(512), nullable=True)
    frozen_cover_path = Column(String(512), nullable=True)
    frozen_duration_seconds = Column(Integer, nullable=True)
    frozen_product_name = Column(String(256), nullable=True)
    frozen_copywriting_text = Column(Text, nullable=True)
    manifest_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    __table_args__ = (UniqueConstraint("creative_version_id"),)

    creative_version = relationship(
        "CreativeVersion",
        back_populates="package_records",
        foreign_keys=[creative_version_id],
    )
    publish_profile = relationship("PublishProfile", foreign_keys=[publish_profile_id])


class CheckRecord(Base):
    """Creative Phase B review record."""
    __tablename__ = "check_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creative_item_id = Column(Integer, ForeignKey("creative_items.id"), nullable=False, index=True)
    creative_version_id = Column(Integer, ForeignKey("creative_versions.id"), nullable=False, index=True)
    conclusion = Column(String(32), nullable=False, index=True)
    rework_type = Column(String(64), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    __table_args__ = (
        CheckConstraint(
            "conclusion IN ('APPROVED', 'REWORK_REQUIRED', 'REJECTED')",
            name="ck_check_records_conclusion",
        ),
        CheckConstraint(
            "conclusion != 'REWORK_REQUIRED' OR rework_type IS NOT NULL",
            name="ck_check_records_rework_type_required",
        ),
    )

    creative_item = relationship(
        "CreativeItem",
        back_populates="check_records",
        foreign_keys=[creative_item_id],
    )
    creative_version = relationship(
        "CreativeVersion",
        back_populates="check_records",
        foreign_keys=[creative_version_id],
    )


class PublishPoolItem(Base):
    """Creative Phase C publishable candidate."""
    __tablename__ = "publish_pool_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creative_item_id = Column(Integer, ForeignKey("creative_items.id"), nullable=False, index=True)
    creative_version_id = Column(Integer, ForeignKey("creative_versions.id"), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="active", index=True)
    invalidation_reason = Column(String(64), nullable=True)
    invalidated_at = Column(DateTime, nullable=True)
    locked_at = Column(DateTime, nullable=True, index=True)
    locked_by_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    __table_args__ = (
        UniqueConstraint("creative_version_id"),
        CheckConstraint(
            "status IN ('active', 'invalidated')",
            name="ck_publish_pool_items_status",
        ),
        CheckConstraint(
            "status != 'invalidated' OR invalidated_at IS NOT NULL",
            name="ck_publish_pool_items_invalidated_at_required",
        ),
        CheckConstraint(
            "locked_by_task_id IS NULL OR locked_at IS NOT NULL",
            name="ck_publish_pool_items_locked_task_requires_locked_at",
        ),
    )

    creative_item = relationship(
        "CreativeItem",
        back_populates="publish_pool_items",
        foreign_keys=[creative_item_id],
    )
    creative_version = relationship(
        "CreativeVersion",
        back_populates="publish_pool_items",
        foreign_keys=[creative_version_id],
    )


class PublishExecutionSnapshot(Base):
    """Frozen publish-planning truth for a Creative publish candidate."""
    __tablename__ = "publish_execution_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pool_item_id = Column(Integer, ForeignKey("publish_pool_items.id"), nullable=False, index=True)
    source_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, unique=True, index=True)
    creative_item_id = Column(Integer, ForeignKey("creative_items.id"), nullable=False, index=True)
    creative_version_id = Column(Integer, ForeignKey("creative_versions.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("publish_profiles.id"), nullable=True, index=True)
    snapshot_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    pool_item = relationship("PublishPoolItem", foreign_keys=[pool_item_id])
    source_task = relationship("Task", foreign_keys=[source_task_id])
    task = relationship("Task", foreign_keys=[task_id])
    creative_item = relationship("CreativeItem", foreign_keys=[creative_item_id])
    creative_version = relationship("CreativeVersion", foreign_keys=[creative_version_id])
    account = relationship("Account", foreign_keys=[account_id])
    profile = relationship("PublishProfile", foreign_keys=[profile_id])


class Product(Base):
    """商品表"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), unique=True, nullable=False, index=True)
    dewu_url = Column(String(512), nullable=True)   # 得物商品页 URL (SP1-06)

    # 解析状态: pending | parsing | parsed | error
    parse_status = Column(String(20), default="pending", nullable=False)

    # 反范式计数（消除列表页 N+1 查询）
    video_count = Column(Integer, default=0, nullable=False)
    copywriting_count = Column(Integer, default=0, nullable=False)
    cover_count = Column(Integer, default=0, nullable=False)
    topic_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    # 关系
    tasks = relationship("Task", foreign_keys="Task.product_id")
    videos = relationship("Video", back_populates="product")
    copywritings = relationship("Copywriting", back_populates="product")
    covers = relationship("Cover", back_populates="product")
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

    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    # 关系
    product = relationship("Product", back_populates="videos")
    covers = relationship("Cover", back_populates="video")


class Copywriting(Base):
    """文案素材表 (SP1-02)"""
    __tablename__ = "copywritings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    name = Column(String(256), nullable=False, server_default="")
    content = Column(Text, nullable=False)
    source_type = Column(String(32), default="manual")
    source_ref = Column(String(256), nullable=True)

    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    # 关系
    product = relationship("Product", back_populates="copywritings")


class Cover(Base):
    """封面素材表 (SP1-03)"""
    __tablename__ = "covers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    name = Column(String(256), nullable=False, server_default="")
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_hash = Column(String(64), index=True, nullable=True)

    created_at = Column(DateTime, default=utc_now_naive)

    # 关系
    video = relationship("Video", back_populates="covers")
    product = relationship("Product", back_populates="covers")


class Audio(Base):
    """音频素材表 (SP1-04)"""
    __tablename__ = "audios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)  # 秒
    file_hash = Column(String(64), index=True, nullable=True)

    created_at = Column(DateTime, default=utc_now_naive)


class Topic(Base):
    """话题表 (SP1-05)"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), unique=True, nullable=False, index=True)
    heat = Column(Integer, default=0)
    source = Column(String(32), default="manual")
    last_synced = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utc_now_naive)


class TaskVideo(Base):
    """任务-视频关联表"""
    __tablename__ = "task_videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint('task_id', 'video_id'),)


class TaskCopywriting(Base):
    """任务-文案关联表"""
    __tablename__ = "task_copywritings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    copywriting_id = Column(Integer, ForeignKey("copywritings.id"), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint('task_id', 'copywriting_id'),)


class TaskCover(Base):
    """任务-封面关联表"""
    __tablename__ = "task_covers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    cover_id = Column(Integer, ForeignKey("covers.id"), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint('task_id', 'cover_id'),)


class TaskAudio(Base):
    """任务-音频关联表"""
    __tablename__ = "task_audios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    audio_id = Column(Integer, ForeignKey("audios.id"), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint('task_id', 'audio_id'),)


class TaskTopic(Base):
    """任务-话题关联表 (SP3-02)"""
    __tablename__ = "task_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint('task_id', 'topic_id'),)


class GlobalTopic(Base):
    """全局 singleton 话题关联表（Phase 6 / PR4 canonical source）"""
    __tablename__ = "global_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint('topic_id'),)


class PublishProfileTopic(Base):
    """配置档-话题关联表（Phase 6 / PR4 canonical source）"""
    __tablename__ = "publish_profile_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("publish_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint('profile_id', 'topic_id'),)


class TopicGroupTopic(Base):
    """话题组-话题关联表（Phase 6 / PR4 canonical source）"""
    __tablename__ = "topic_group_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("topic_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    __table_args__ = (UniqueConstraint('group_id', 'topic_id'),)


class ProductTopic(Base):
    """商品-话题关联表"""
    __tablename__ = "product_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint('product_id', 'topic_id'),)


class CompositionJob(Base):
    """合成任务表 (BE-TM-02)"""
    __tablename__ = "composition_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_type = Column(String(32), nullable=True)       # 'coze' / 'local_ffmpeg'
    workflow_id = Column(String(128), nullable=True)        # Coze workflow_id
    external_job_id = Column(String(128), nullable=True)    # Coze execute_id
    status = Column(String(32), default="pending", index=True)
    progress = Column(Integer, default=0)
    output_video_path = Column(String(512), nullable=True)
    output_video_url = Column(String(512), nullable=True)
    error_msg = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    # 关系
    task = relationship("Task", back_populates="composition_jobs")


class PublishLog(Base):
    """发布日志表"""
    __tablename__ = "publish_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)

    status = Column(String(32), nullable=False)  # started, success, failed
    message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now_naive, index=True)

    # 关系
    task = relationship("Task", back_populates="logs")


class PublishConfig(Base):
    """发布配置表（遗留兼容模型，调度真相将逐步收口到 ScheduleConfig）"""
    __tablename__ = "publish_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), default="default")
    interval_minutes = Column(Integer, default=30)
    start_hour = Column(Integer, default=9)
    end_hour = Column(Integer, default=22)
    max_per_account_per_day = Column(Integer, default=5)
    shuffle = Column(Boolean, default=False)
    auto_start = Column(Boolean, default=False)
    global_topic_ids = Column(Text, default='[]')  # legacy singleton topic surface；不再代表调度 canonical truth

    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class PublishProfile(Base):
    """合成配置档表"""
    __tablename__ = "publish_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False, index=True)
    is_default = Column(Boolean, default=False)

    # 合成配置
    composition_mode = Column(String(32), default="none")   # 'none' / 'coze' / 'local_ffmpeg'
    coze_workflow_id = Column(String(128), nullable=True)
    composition_params = Column(Text, nullable=True)        # Opaque JSON 配置；Phase 6 结论为 keep-json

    # 话题配置
    global_topic_ids = Column(Text, default="[]")           # 当前 TaskAssembler 唯一会自动合并的 profile-level default topics

    # 重试配置
    auto_retry = Column(Boolean, default=True)
    max_retry_count = Column(Integer, default=3)

    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    # 关系
    topic_links = relationship("PublishProfileTopic", passive_deletes=True, order_by="PublishProfileTopic.sort_order")


class ScheduleConfig(Base):
    """调度配置表（全局单例，作为调度配置的 canonical truth）"""
    __tablename__ = "schedule_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), default="default")
    start_hour = Column(Integer, default=9)
    end_hour = Column(Integer, default=22)
    interval_minutes = Column(Integer, default=30)
    max_per_account_per_day = Column(Integer, default=5)
    shuffle = Column(Boolean, default=False)
    auto_start = Column(Boolean, default=False)
    publish_scheduler_mode = Column(String(16), default="task")
    publish_pool_kill_switch = Column(Boolean, default=False)
    publish_pool_shadow_read = Column(Boolean, default=False)

    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class RemoteAuthSession(Base):
    """本地机器授权会话表（仅持久化 non-secret state）"""
    __tablename__ = "remote_auth_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    auth_state = Column(String(32), default="unauthenticated", nullable=False, index=True)
    remote_user_id = Column(String(128), nullable=True, index=True)
    display_name = Column(String(256), nullable=True)
    license_status = Column(String(32), nullable=True, index=True)
    entitlements_snapshot = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)
    offline_grace_until = Column(DateTime, nullable=True)
    denial_reason = Column(String(64), nullable=True)
    device_id = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)


class TopicGroup(Base):
    """话题组表 (话题模板)"""
    __tablename__ = "topic_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False, index=True)
    topic_ids = Column(Text, nullable=False, default='[]')  # 命名话题列表 JSON；当前 CRUD-only，不会自动注入 task assembly

    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    # 关系
    topic_links = relationship("TopicGroupTopic", passive_deletes=True, order_by="TopicGroupTopic.sort_order")


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(16), nullable=False)  # INFO, WARNING, ERROR
    module = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now_naive, index=True)


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
    migration_010 = importlib.import_module("migrations.010_dewu_url_unique")
    await migration_010.run_migration(engine)
    migration_011 = importlib.import_module("migrations.011_media_file_hash")
    await migration_011.run_migration(engine)
    migration_012 = importlib.import_module("migrations.012_product_redesign")
    await migration_012.run_migration(engine)
    migration_013 = importlib.import_module("migrations.013_cover_name")
    await migration_013.run_migration(engine)
    migration_014 = importlib.import_module("migrations.014_copywriting_name")
    await migration_014.run_migration(engine)
    migration_015 = importlib.import_module("migrations.015_topic_groups")
    await migration_015.run_migration(engine)
    migration_016 = importlib.import_module("migrations.016_task_composition_fields")
    await migration_016.run_migration(engine)
    migration_017 = importlib.import_module("migrations.017_publish_profiles")
    await migration_017.run_migration(engine)
    migration_018 = importlib.import_module("migrations.018_composition_jobs")
    await migration_018.run_migration(engine)
    migration_019 = importlib.import_module("migrations.019_schedule_config")
    await migration_019.run_migration(engine)
    migration_020 = importlib.import_module("migrations.020_task_new_fields")
    await migration_020.run_migration(engine)
    migration_021 = importlib.import_module("migrations.021_task_resource_tables")
    await migration_021.run_migration(engine)
    migration_022 = importlib.import_module("migrations.022_topic_relation_sources")
    await migration_022.run_migration(engine)
    migration_023 = importlib.import_module("migrations.023_remote_auth_sessions")
    await migration_023.run_migration(engine)
    migration_024 = importlib.import_module("migrations.024_creative_phase_a_skeleton")
    await migration_024.run_migration(engine)
    migration_025 = importlib.import_module("migrations.025_creative_phase_b_review_invariants")
    await migration_025.run_migration(engine)
    migration_026 = importlib.import_module("migrations.026_creative_phase_b_composition_writeback")
    await migration_026.run_migration(engine)
    migration_027 = importlib.import_module("migrations.027_creative_phase_c_publish_pool")
    await migration_027.run_migration(engine)
    migration_028 = importlib.import_module("migrations.028_creative_phase_c_publish_execution_snapshot")
    await migration_028.run_migration(engine)
    migration_029 = importlib.import_module("migrations.029_creative_phase_c_scheduler_cutover")
    await migration_029.run_migration(engine)
    migration_030 = importlib.import_module("migrations.030_task_optional_account")
    await migration_030.run_migration(engine)
    migration_031 = importlib.import_module("migrations.031_creative_workdriven_phase1")
    await migration_031.run_migration(engine)
    migration_032 = importlib.import_module("migrations.032_creative_input_snapshot_layer")
    await migration_032.run_migration(engine)
    migration_033 = importlib.import_module("migrations.033_creative_domain_model_foundation")
    await migration_033.run_migration(engine)
    migration_034 = importlib.import_module("migrations.034_creative_phase3_freeze_contract")
    await migration_034.run_migration(engine)
    migration_035 = importlib.import_module("migrations.035_creative_phase4_snapshot_retirement")
    await migration_035.run_migration(engine)

    logger.info("数据库初始化完成")


async def get_db():
    """获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
