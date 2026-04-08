"""
得物掘金工具 - Pydantic Schemas
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
import json


# ============ 枚举定义 ============

class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOGGING_IN = "logging_in"
    SESSION_EXPIRED = "session_expired"
    DISABLED = "disabled"


class ConnectionStatus(str, Enum):
    """
    连接流程状态枚举 (原 LoginStatus)

    用于 SSE 实时推送和连接流程状态管理。
    状态流转: idle -> waiting_phone -> code_sent -> waiting_verify -> verifying -> success/error
    """
    IDLE = "idle"
    WAITING_PHONE = "waiting_phone"  # 等待输入手机号
    CODE_SENT = "code_sent"  # 验证码已发送
    WAITING_VERIFY = "waiting_verify"  # 等待验证（已发送验证码）
    VERIFYING = "verifying"  # 正在验证
    SUCCESS = "success"  # 连接成功
    ERROR = "error"  # 连接失败


# 向后兼容别名
LoginStatus = ConnectionStatus


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"


class PublishStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"


# ============ 账号 Schema ============

class AccountBase(BaseModel):
    account_id: str = Field(..., description="平台账号ID")
    account_name: str = Field(..., description="账号名称")


class AccountCreate(AccountBase):
    """创建账号"""
    phone: Optional[str] = Field(None, min_length=11, max_length=11, description="明文手机号，后端加密存储")
    tags: List[str] = Field(default_factory=list)
    remark: Optional[str] = None


class AccountUpdate(BaseModel):
    """更新账号"""
    account_name: Optional[str] = None
    status: Optional[AccountStatus] = None
    cookie: Optional[str] = None
    phone: Optional[str] = Field(None, min_length=11, max_length=11, description="明文手机号，后端加密存储")
    tags: Optional[List[str]] = None
    remark: Optional[str] = None


class AccountResponse(AccountBase):
    """账号响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: AccountStatus
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # 扩展字段
    phone_masked: Optional[str] = None          # "138****8000"
    dewu_nickname: Optional[str] = None
    dewu_uid: Optional[str] = None
    avatar_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    remark: Optional[str] = None
    session_expires_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    login_fail_count: int = 0

    @model_validator(mode="before")
    @classmethod
    def _parse_tags(cls, data: Any) -> Any:
        """将数据库中的 JSON 字符串解析为 List[str]。"""
        # ORM 对象时，从属性读取
        tags_raw = data.get("tags") if isinstance(data, dict) else getattr(data, "tags", None)
        if isinstance(tags_raw, str):
            try:
                parsed = json.loads(tags_raw)
            except (ValueError, TypeError):
                parsed = []
            if isinstance(data, dict):
                data["tags"] = parsed
            else:
                # ORM 对象不可直接赋值，转为 dict 再处理
                data = {
                    c.key: getattr(data, c.key)
                    for c in data.__class__.__table__.columns
                }
                data["tags"] = parsed
        return data


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    success: bool
    is_valid: bool
    message: str
    expires_at: Optional[datetime] = None


class BatchHealthCheckRequest(BaseModel):
    """批量健康检查请求"""
    account_ids: Optional[List[int]] = Field(
        None, description="指定账号ID列表，为空则检测所有"
    )
    concurrency: int = Field(
        default=1, ge=1, le=3,
        description="并发数（默认串行，最大3）"
    )
    interval_seconds: int = Field(
        default=2, ge=0, le=10,
        description="每次检测间隔秒数"
    )
    skip_inactive: bool = Field(
        default=True,
        description="跳过 inactive/disabled 状态的账号"
    )


class BatchHealthCheckResultItem(BaseModel):
    """单个账号检测结果"""
    account_id: int
    account_name: str
    previous_status: str
    current_status: str
    is_valid: bool
    message: str
    checked_at: datetime


class BatchHealthCheckResponse(BaseModel):
    """批量健康检查响应"""
    total: int
    checked: int
    skipped: int
    valid_count: int
    expired_count: int
    error_count: int
    results: List[BatchHealthCheckResultItem]
    started_at: datetime
    completed_at: datetime


class BatchHealthCheckStatusResponse(BaseModel):
    """批量检测进度"""
    in_progress: bool
    progress: int = 0
    total: int = 0
    current_account_name: Optional[str] = None
    started_at: Optional[datetime] = None
    logs: List[str] = Field(default_factory=list)


class AccountLoginRequest(BaseModel):
    """账号登录请求"""
    account_id: str


class AccountTestRequest(BaseModel):
    """账号测试请求"""
    account_id: int


class ConnectionRequest(BaseModel):
    """得物账号连接请求 (手机验证码方式)"""
    phone: str = Field(..., min_length=11, max_length=11, description="手机号")
    code: str = Field(..., min_length=4, max_length=6, description="验证码")


# 向后兼容别名
LoginRequest = ConnectionRequest


class ConnectionResponse(BaseModel):
    """连接响应"""
    success: bool
    message: str
    status: str = "inactive"
    storage_state: Optional[str] = None


# 向后兼容别名
LoginResponse = ConnectionResponse


class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: Optional[str] = Field(None, min_length=11, max_length=11, description="手机号（11位），为空则使用已存储的手机号")


class SendCodeResponse(BaseModel):
    """发送验证码响应"""
    success: bool
    message: str
    status: str = "waiting_phone"


class VerifyCodeRequest(BaseModel):
    """验证码登录请求"""
    code: str = Field(..., min_length=4, max_length=6, description="短信验证码（4-6位）")


class VerifyCodeResponse(BaseModel):
    """验证码登录响应"""
    success: bool
    message: str
    status: str = "inactive"


class ConnectionStatusResponse(BaseModel):
    """连接状态响应"""
    is_connected: bool
    status: ConnectionStatus
    last_login: Optional[datetime] = None
    message: str = ""


# 向后兼容别名
LoginStatusResponse = ConnectionStatusResponse


class ConnectionStreamEvent(BaseModel):
    """SSE 连接状态事件"""
    event: str = "status_update"
    data: "ConnectionStreamData"


class ConnectionStreamData(BaseModel):
    """SSE 连接状态数据"""
    status: ConnectionStatus
    message: str
    progress: Optional[int] = None  # 0-100 进度百分比


# 向后兼容别名
LoginStreamEvent = ConnectionStreamEvent
LoginStreamData = ConnectionStreamData


class AccountStats(BaseModel):
    """账号统计"""
    total_accounts: int
    active_accounts: int
    today_published: int = 0
    total_videos: int = 0


# ============ 任务 Schema ============

class TaskCreate(BaseModel):
    """创建任务"""
    account_id: int
    product_id: Optional[int] = None
    video_id: Optional[int] = None
    copywriting_id: Optional[int] = None
    audio_id: Optional[int] = None
    cover_id: Optional[int] = None


class TaskUpdate(BaseModel):
    """更新任务"""
    account_id: Optional[int] = None
    product_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = None


class TaskResponse(BaseModel):
    """任务响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    product_id: Optional[int] = None
    video_id: Optional[int] = None
    copywriting_id: Optional[int] = None
    audio_id: Optional[int] = None
    cover_id: Optional[int] = None
    topic_ids: List[int] = Field(default_factory=list)
    status: TaskStatus
    publish_time: Optional[datetime] = None
    error_msg: Optional[str] = None
    priority: int
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _resolve_topic_ids(cls, data: Any) -> Any:
        """从 ORM 关系中读取 topics 列表填充 topic_ids。"""
        topics_raw = (
            data.get("topics") if isinstance(data, dict)
            else getattr(data, "topics", None)
        )
        if topics_raw is not None and not isinstance(topics_raw, list):
            return data
        if topics_raw:
            ids = [t.id if hasattr(t, "id") else t for t in topics_raw]
            if isinstance(data, dict):
                data["topic_ids"] = ids
            else:
                data = {
                    c.key: getattr(data, c.key)
                    for c in data.__class__.__table__.columns
                }
                data["topic_ids"] = ids
        return data


class TaskListResponse(BaseModel):
    """任务列表响应"""
    total: int
    items: List[TaskResponse]


class TaskPublishRequest(BaseModel):
    """立即发布请求"""
    task_id: int


class TaskBatchCreateRequest(BaseModel):
    """批量创建任务"""
    tasks: List[TaskCreate]


class AssembleTasksRequest(BaseModel):
    """组装任务请求 — 多视频+多账号自动分配"""
    video_ids: List[int] = Field(..., min_length=1)
    account_ids: List[int] = Field(..., min_length=1)
    strategy: str = Field(default="round_robin", pattern="^(round_robin|manual)$")
    copywriting_mode: str = Field(default="auto_match", pattern="^(auto_match|manual)$")


# ============ 商品 Schema ============

class ProductCreate(BaseModel):
    """创建商品 — 仅接受分享文本，后端解析 dewu_url"""
    share_text: str = Field(..., min_length=1, max_length=2048)


class ProductUpdate(BaseModel):
    """更新商品 — 仅允许修改名称"""
    name: Optional[str] = Field(None, min_length=1, max_length=256)


class ProductResponse(BaseModel):
    """商品响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    dewu_url: Optional[str] = None
    parse_status: str
    video_count: int = 0
    copywriting_count: int = 0
    cover_count: int = 0
    topic_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    """商品列表响应"""
    total: int
    items: List[ProductResponse]


class ProductDetailResponse(ProductResponse):
    """商品详情响应（含全部关联素材）"""
    videos: List["VideoResponse"] = []
    covers: List["CoverResponse"] = []
    copywritings: List["CopywritingResponse"] = []
    topics: List["TopicResponse"] = []


# ============ Video Schema (SP1-01) ============

class VideoCreate(BaseModel):
    """创建视频"""
    name: str = Field(..., min_length=1, max_length=256)
    file_path: str = Field(..., min_length=1, max_length=512)
    product_id: Optional[int] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None

    @field_validator('file_path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        if '..' in v:
            raise ValueError('路径不能包含 ..')
        return v


class VideoUpdate(BaseModel):
    """更新视频"""
    name: Optional[str] = None
    product_id: Optional[int] = None


class VideoResponse(BaseModel):
    """视频响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    name: str
    file_path: str
    file_size: Optional[int] = None
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_hash: Optional[str] = None
    source_type: str
    file_exists: bool = True
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _resolve_product_name(cls, data: Any) -> Any:
        """从 ORM 关系中读取 product.name 填充 product_name。"""
        product = (
            data.get("product") if isinstance(data, dict)
            else getattr(data, "product", None)
        )
        if not isinstance(data, dict):
            data = {
                c.key: getattr(data, c.key)
                for c in data.__class__.__table__.columns
            }
        if product and hasattr(product, "name"):
            data["product_name"] = product.name
        return data


class VideoListResponse(BaseModel):
    """视频列表响应"""
    total: int
    items: List[VideoResponse]


# ============ Copywriting Schema (SP1-02) ============

class CopywritingCreate(BaseModel):
    """创建文案"""
    name: Optional[str] = Field(None, max_length=256, description="文案名称，为空则取 content 前 50 字")
    content: str = Field(..., min_length=1)
    product_id: Optional[int] = None
    source_type: str = Field(default="manual", max_length=32)
    source_ref: Optional[str] = None


class CopywritingUpdate(BaseModel):
    """更新文案"""
    name: Optional[str] = Field(None, max_length=256)
    content: Optional[str] = None
    product_id: Optional[int] = None
    source_type: Optional[str] = None
    source_ref: Optional[str] = None


class CopywritingResponse(BaseModel):
    """文案响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    name: str = ""
    content: str
    source_type: str
    source_ref: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _resolve_product_name(cls, data: Any) -> Any:
        """从 ORM 关系中读取 product.name 填充 product_name。"""
        product = (
            data.get("product") if isinstance(data, dict)
            else getattr(data, "product", None)
        )
        if product and hasattr(product, "name"):
            if isinstance(data, dict):
                data["product_name"] = product.name
            else:
                data = {
                    c.key: getattr(data, c.key)
                    for c in data.__class__.__table__.columns
                }
                data["product_name"] = product.name
        return data


class CopywritingListResponse(BaseModel):
    """文案列表响应"""
    total: int
    items: List[CopywritingResponse]


# ============ Cover Schema (SP1-03) ============

class CoverCreate(BaseModel):
    """创建封面"""
    file_path: str = Field(..., min_length=1, max_length=512)
    video_id: Optional[int] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class CoverResponse(BaseModel):
    """封面响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: Optional[int] = None
    product_id: Optional[int] = None
    name: str = ""
    file_path: str
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime


# ============ Audio Schema (SP1-04) ============

class AudioCreate(BaseModel):
    """创建音频"""
    name: str = Field(..., min_length=1, max_length=256)
    file_path: str = Field(..., min_length=1, max_length=512)
    file_size: Optional[int] = None
    duration: Optional[int] = None


class AudioResponse(BaseModel):
    """音频响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    file_path: str
    file_size: Optional[int] = None
    duration: Optional[int] = None
    created_at: datetime


# ============ Topic Schema (SP1-05) ============

class TopicCreate(BaseModel):
    """创建话题"""
    name: str = Field(..., min_length=1, max_length=256)
    heat: int = Field(default=0, ge=0)
    source: str = Field(default="manual", max_length=32)


class TopicResponse(BaseModel):
    """话题响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    heat: int
    source: str
    last_synced: Optional[datetime] = None
    created_at: datetime


class TopicListResponse(BaseModel):
    """话题列表响应"""
    total: int
    items: List[TopicResponse]


# ============ 发布控制 Schema ============

class PublishConfigRequest(BaseModel):
    """发布配置请求"""
    interval_minutes: int = Field(default=30, ge=1, le=1440)
    start_hour: int = Field(default=9, ge=0, le=23)
    end_hour: int = Field(default=22, ge=0, le=23)
    max_per_account_per_day: int = Field(default=5, ge=1, le=100)
    shuffle: bool = False
    auto_start: bool = False


class PublishConfigResponse(BaseModel):
    """发布配置响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    interval_minutes: int
    start_hour: int
    end_hour: int
    max_per_account_per_day: int
    shuffle: bool
    auto_start: bool


class PublishControlRequest(BaseModel):
    """发布控制请求"""
    action: str = Field(..., description="start, pause, stop")


class PublishStatusResponse(BaseModel):
    """发布状态响应"""
    status: PublishStatus
    current_task_id: Optional[int] = None
    total_pending: int = 0
    total_success: int = 0
    total_failed: int = 0


# ============ 系统 Schema ============

class SystemStats(BaseModel):
    """系统统计"""
    total_accounts: int
    active_accounts: int
    total_tasks: int
    pending_tasks: int
    success_tasks: int
    failed_tasks: int
    total_products: int


class SystemLogResponse(BaseModel):
    """系统日志响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    level: str
    module: Optional[str] = None
    message: str
    details: Optional[str] = None
    created_at: datetime


class SystemLogListResponse(BaseModel):
    """系统日志列表响应"""
    total: int
    items: List[SystemLogResponse]


class BackupRequest(BaseModel):
    """备份请求"""
    include_logs: bool = False


# ============ 预览 Schema ============

class PreviewCloseRequest(BaseModel):
    """关闭预览浏览器请求"""
    save_session: bool = False


class PreviewStatusResponse(BaseModel):
    """预览状态响应"""
    is_open: bool
    account_id: Optional[int] = None


# ============ 话题组 Schema ============

class TopicGroupCreate(BaseModel):
    """创建话题组"""
    name: str = Field(..., min_length=1, max_length=128)
    topic_ids: List[int] = Field(default_factory=list, description="话题ID列表")


class TopicGroupUpdate(BaseModel):
    """更新话题组"""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    topic_ids: Optional[List[int]] = Field(None, description="话题ID列表")


class TopicGroupResponse(BaseModel):
    """话题组响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    topic_ids: List[int]
    topics: List["TopicResponse"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _parse_topic_ids(cls, data: Any) -> Any:
        """将数据库中的 JSON 字符串解析为 List[int]。"""
        raw = data.get("topic_ids") if isinstance(data, dict) else getattr(data, "topic_ids", None)
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except (ValueError, TypeError):
                parsed = []
            if isinstance(data, dict):
                data["topic_ids"] = parsed
            else:
                data = {c.key: getattr(data, c.key) for c in data.__class__.__table__.columns}
                data["topic_ids"] = parsed
        return data


class TopicGroupListResponse(BaseModel):
    """话题组列表响应"""
    total: int
    items: List[TopicGroupResponse]


# ============ 全局话题 Schema (SP4-03) ============

class GlobalTopicRequest(BaseModel):
    """设置全局话题请求"""
    topic_ids: List[int] = Field(..., description="话题ID列表")


class GlobalTopicResponse(BaseModel):
    """全局话题响应"""
    topic_ids: List[int]
    topics: List[TopicResponse]


# ============ 批量删除 Schema ============

class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    ids: List[int]


class BatchDeleteResponse(BaseModel):
    """批量删除响应"""
    deleted: int
    skipped: int
    skipped_ids: List[int]


# ============ 通用响应 ============

class ApiResponse(BaseModel):
    """通用 API 响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[dict] = None


# ============ 商品素材解析 Schema ============

class ParseMaterialsResponse(BaseModel):
    """商品素材解析响应"""
    success: bool
    product_id: int
    title: str
    topics: List[str]
    videos_downloaded: int
    covers_downloaded: int
    errors: List[str] = Field(default_factory=list)
