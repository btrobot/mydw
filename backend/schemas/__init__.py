"""
得物掘金工具 - Pydantic Schemas
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator, computed_field
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
    DRAFT = "draft"
    COMPOSING = "composing"
    READY = "ready"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskKind(str, Enum):
    COMPOSITION = "composition"
    PUBLISH = "publish"


class CreativeStatus(str, Enum):
    PENDING_INPUT = "PENDING_INPUT"
    WAITING_REVIEW = "WAITING_REVIEW"
    APPROVED = "APPROVED"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    REJECTED = "REJECTED"


class CreativeReviewConclusion(str, Enum):
    APPROVED = "APPROVED"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    REJECTED = "REJECTED"


class PublishPoolStatus(str, Enum):
    ACTIVE = "active"
    INVALIDATED = "invalidated"


class PublishSchedulerMode(str, Enum):
    TASK = "task"
    POOL = "pool"


class CompositionJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
    tags: List[str] = Field(
        default_factory=list,
        description="多值账号标签；Phase 6 最终结论为 normalize-later，当前仍以 JSON 数组存储。",
    )
    remark: Optional[str] = None


class AccountUpdate(BaseModel):
    """更新账号"""
    account_name: Optional[str] = None
    status: Optional[AccountStatus] = None
    cookie: Optional[str] = None
    phone: Optional[str] = Field(None, min_length=11, max_length=11, description="明文手机号，后端加密存储")
    tags: Optional[List[str]] = Field(
        None,
        description="多值账号标签；Phase 6 最终结论为 normalize-later，当前仍以 JSON 数组存储。",
    )
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
    tags: List[str] = Field(
        default_factory=list,
        description="多值账号标签；当前仍从 JSON 数组解析，后续进入 normalize-later 方案。",
    )
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

class TaskCreateRequest(BaseModel):
    """创建任务（资源集合模型）"""
    video_ids: List[int] = Field(..., min_length=1, description="视频ID列表")
    copywriting_ids: List[int] = Field(default_factory=list, description="文案ID列表")
    cover_ids: List[int] = Field(default_factory=list, description="封面ID列表")
    audio_ids: List[int] = Field(default_factory=list, description="音频ID列表")
    topic_ids: List[int] = Field(default_factory=list, description="话题ID列表")
    account_ids: List[int] = Field(..., min_length=1, description="账号ID列表")
    profile_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=256)
    scheduled_time: Optional[datetime] = None
    priority: Optional[int] = 1

    @field_validator("video_ids", "copywriting_ids", "cover_ids", "audio_ids", "topic_ids", "account_ids")
    @classmethod
    def deduplicate_ids(cls, v: List[int]) -> List[int]:
        """保序去重，防止 UniqueConstraint 异常。"""
        return list(dict.fromkeys(v))


class TaskCreate(BaseModel):
    """创建单个任务（内部/兼容用途；非 authoritative public create contract）"""
    account_id: int
    video_id: Optional[int] = None
    copywriting_id: Optional[int] = None
    audio_id: Optional[int] = None
    cover_id: Optional[int] = None
    profile_id: Optional[int] = None
    name: Optional[str] = None
    source_video_ids: Optional[str] = Field(
        None,
        description="legacy migration-observation field；authoritative source 已是 task_videos，Phase 6 结论为 delete-ready-later。",
    )
    composition_template: Optional[str] = None
    composition_params: Optional[str] = Field(
        None,
        description="task 级 opaque JSON params；Phase 6 结论为 keep-json。",
    )
    scheduled_time: Optional[datetime] = None
    priority: Optional[int] = 1
    topic_ids: Optional[str] = None


class TaskUpdate(BaseModel):
    """更新任务"""
    account_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = None
    profile_id: Optional[int] = None
    failed_at_status: Optional[str] = Field(None, max_length=32)
    name: Optional[str] = Field(None, max_length=256)


class TaskResponse(BaseModel):
    """任务响应（authoritative 资源集合模型；legacy single-resource 字段不再公开承诺）"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    creative_item_id: Optional[int] = None
    creative_version_id: Optional[int] = None
    task_kind: Optional[TaskKind] = None
    video_ids: List[int] = Field(default_factory=list)
    copywriting_ids: List[int] = Field(default_factory=list)
    cover_ids: List[int] = Field(default_factory=list)
    audio_ids: List[int] = Field(default_factory=list)
    topic_ids: List[int] = Field(default_factory=list)
    status: TaskStatus
    publish_time: Optional[datetime] = None
    error_msg: Optional[str] = None
    priority: int

    # 合成相关字段
    name: Optional[str] = None
    composition_template: Optional[str] = None
    composition_params: Optional[str] = Field(
        None,
        description="task 级 opaque JSON params；Phase 6 结论为 keep-json。",
    )
    composition_job_id: Optional[int] = None
    final_video_path: Optional[str] = None
    final_video_duration: Optional[int] = None
    final_video_size: Optional[int] = None
    scheduled_time: Optional[datetime] = None
    retry_count: int = 0
    dewu_video_id: Optional[str] = None
    dewu_video_url: Optional[str] = None

    # 发布档案关联字段
    profile_id: Optional[int] = None
    batch_id: Optional[str] = None
    failed_at_status: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _resolve_resource_ids(cls, data: Any) -> Any:
        """从 ORM 关系中提取各资源 ID 列表。"""
        if isinstance(data, dict):
            return data

        result = {
            c.key: getattr(data, c.key)
            for c in data.__class__.__table__.columns
        }

        for attr, key in [
            ("videos", "video_ids"),
            ("copywritings", "copywriting_ids"),
            ("covers", "cover_ids"),
            ("audios", "audio_ids"),
            ("topics", "topic_ids"),
        ]:
            items = getattr(data, attr, None)
            if items:
                result[key] = [item.id for item in items]
            else:
                result[key] = []

        return result

    @computed_field
    @property
    def account_name(self) -> Optional[str]:
        """账号名称"""
        return self.account.account_name if hasattr(self, 'account') and self.account else None

    @computed_field
    @property
    def upload_url(self) -> Optional[str]:
        """上传URL（别名）"""
        return self.dewu_video_url


class TaskListResponse(BaseModel):
    """??????"""
    total: int
    items: List[TaskResponse]


class PackageRecordResponse(BaseModel):
    """??????Phase A ?????"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    creative_version_id: int
    package_status: str
    manifest_json: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CheckRecordResponse(BaseModel):
    """Creative Phase B review record."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    creative_item_id: int
    creative_version_id: int
    conclusion: CreativeReviewConclusion
    rework_type: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PublishPoolItemResponse(BaseModel):
    """Creative Phase C publish-pool item projection."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    creative_item_id: int
    creative_version_id: int
    status: PublishPoolStatus
    invalidation_reason: Optional[str] = None
    invalidated_at: Optional[datetime] = None
    creative_no: Optional[str] = None
    creative_title: Optional[str] = None
    creative_status: Optional[CreativeStatus] = None
    creative_current_version_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class PublishPoolListResponse(BaseModel):
    """Paginated publish-pool list response."""

    total: int
    items: List[PublishPoolItemResponse]


class PublishExecutionSnapshotResponse(BaseModel):
    """Frozen publish-planning snapshot for a publish task."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    pool_item_id: int
    source_task_id: int
    task_id: Optional[int] = None
    creative_item_id: int
    creative_version_id: int
    account_id: int
    profile_id: Optional[int] = None
    snapshot_json: str
    created_at: datetime
    updated_at: datetime


class CreativeVersionSummaryResponse(BaseModel):
    """?????????Phase A?"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    creative_item_id: int
    parent_version_id: Optional[int] = None
    version_no: int
    version_type: str
    title: Optional[str] = None
    package_record_id: Optional[int] = None
    is_current: bool = False
    latest_check: Optional[CheckRecordResponse] = None
    created_at: datetime
    updated_at: datetime


class CreativeItemResponse(BaseModel):
    """???????Phase A?"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    creative_no: str
    title: Optional[str] = None
    status: CreativeStatus
    current_version_id: Optional[int] = None
    latest_version_no: int = 0
    generation_error_msg: Optional[str] = None
    generation_failed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CreativeWorkbenchItemResponse(BaseModel):
    """Creative workbench list item for Phase A."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    creative_no: str
    title: Optional[str] = None
    status: CreativeStatus
    current_version_id: Optional[int] = None
    generation_error_msg: Optional[str] = None
    generation_failed_at: Optional[datetime] = None
    updated_at: datetime


class CreativeWorkbenchListResponse(BaseModel):
    """Paginated Creative workbench list response for Phase A."""

    total: int
    items: List[CreativeWorkbenchItemResponse]


class CreativeCurrentVersionResponse(BaseModel):
    """Current-version projection for the Creative detail endpoint."""

    id: int
    version_no: int
    title: Optional[str] = None
    parent_version_id: Optional[int] = None
    package_record_id: Optional[int] = None
    latest_check: Optional[CheckRecordResponse] = None


class CreativeReviewSummaryResponse(BaseModel):
    """Effective review summary for the current Creative version."""

    current_version_id: Optional[int] = None
    current_check: Optional[CheckRecordResponse] = None
    total_checks: int = 0


class CreativeApproveRequest(BaseModel):
    version_id: int
    note: Optional[str] = None


class CreativeRejectRequest(BaseModel):
    version_id: int
    note: Optional[str] = None


class CreativeReworkRequest(BaseModel):
    version_id: int
    rework_type: Optional[str] = None
    note: Optional[str] = None


class CreativeReviewActionResponse(BaseModel):
    creative_id: int
    creative_status: CreativeStatus
    current_version_id: Optional[int] = None
    check: CheckRecordResponse


class CreativeDetailResponse(BaseModel):
    """Creative detail response for the Phase A workbench/detail flow."""

    id: int
    creative_no: str
    title: Optional[str] = None
    status: CreativeStatus
    current_version_id: Optional[int] = None
    current_version: Optional[CreativeCurrentVersionResponse] = None
    versions: List[CreativeVersionSummaryResponse] = Field(default_factory=list)
    review_summary: Optional[CreativeReviewSummaryResponse] = None
    linked_task_ids: List[int] = Field(default_factory=list)
    generation_error_msg: Optional[str] = None
    generation_failed_at: Optional[datetime] = None
    updated_at: datetime


# ============ CompositionJob Schema (BE-TM-02) ============

class CompositionJobResponse(BaseModel):
    """合成任务响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    workflow_type: Optional[str] = None
    workflow_id: Optional[str] = None
    external_job_id: Optional[str] = None
    status: CompositionJobStatus
    progress: int
    output_video_path: Optional[str] = None
    output_video_url: Optional[str] = None
    error_msg: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TaskPublishRequest(BaseModel):
    """立即发布请求"""
    task_id: int


class TaskBatchCreateRequest(BaseModel):
    """批量创建任务"""
    tasks: List[TaskCreate]


class AssembleTasksRequest(BaseModel):
    """组装任务请求（已废弃，保留兼容；authoritative 语义以 TaskCreateRequest 为准）"""
    video_ids: List[int] = Field(..., min_length=1)
    account_ids: List[int] = Field(..., min_length=1)
    profile_id: Optional[int] = None


class BatchAssembleRequest(BaseModel):
    """批量组装任务请求（已废弃；authoritative 语义以 TaskCreateRequest 为准）"""
    video_ids: List[int] = Field(..., min_length=1, description="视频ID列表")
    copywriting_ids: List[int] = Field(default_factory=list, description="文案ID列表")
    cover_ids: List[int] = Field(default_factory=list, description="封面ID列表")
    audio_ids: List[int] = Field(default_factory=list, description="音频ID列表")
    account_ids: List[int] = Field(..., min_length=1, description="账号ID列表")
    profile_id: Optional[int] = None


# ============ 商品 Schema ============

class ProductCreate(BaseModel):
    """创建商品，请求中必须同时提供商品名称和分享文本。"""
    name: str = Field(..., min_length=1, max_length=256)
    share_text: str = Field(..., min_length=1, max_length=2048)

    @field_validator("name", "share_text")
    @classmethod
    def strip_and_validate_non_blank(cls, v: str) -> str:
        value = v.strip()
        if not value:
            raise ValueError("value cannot be blank")
        return value


class ProductUpdate(BaseModel):
    """更新商品，目前只允许修改商品名称。"""
    name: Optional[str] = Field(None, min_length=1, max_length=256)

    @field_validator("name")
    @classmethod
    def strip_and_validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        value = v.strip()
        if not value:
            raise ValueError("name cannot be blank")
        return value


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


class ProductMaterialsResponse(BaseModel):
    """商品关联素材响应"""
    product: ProductResponse
    videos: List["VideoResponse"] = []
    copywritings: List["CopywritingResponse"] = []
    covers: List["CoverResponse"] = []


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
    """发布配置请求（遗留兼容 schema，后续由 ScheduleConfigRequest 取代）"""
    interval_minutes: int = Field(default=30, ge=1, le=1440)
    start_hour: int = Field(default=9, ge=0, le=23)
    end_hour: int = Field(default=22, ge=0, le=23)
    max_per_account_per_day: int = Field(default=5, ge=1, le=100)
    shuffle: bool = False
    auto_start: bool = False
    publish_scheduler_mode: PublishSchedulerMode = PublishSchedulerMode.TASK
    publish_pool_kill_switch: bool = False
    publish_pool_shadow_read: bool = False


class PublishConfigResponse(BaseModel):
    """发布配置响应（遗留兼容 schema，后续由 ScheduleConfigResponse 取代）"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    interval_minutes: int
    start_hour: int
    end_hour: int
    max_per_account_per_day: int
    shuffle: bool
    auto_start: bool
    publish_scheduler_mode: PublishSchedulerMode = PublishSchedulerMode.TASK
    publish_pool_kill_switch: bool = False
    publish_pool_shadow_read: bool = False


# ============ 调度配置 Schema (替代 PublishConfig) ============

class ScheduleConfigRequest(BaseModel):
    """调度配置请求"""
    start_hour: int = Field(default=9, ge=0, le=23, description="开始小时（0-23）")
    end_hour: int = Field(default=22, ge=0, le=23, description="结束小时（0-23）")
    interval_minutes: int = Field(default=30, ge=1, le=1440, description="上传间隔（分钟）")
    max_per_account_per_day: int = Field(default=5, ge=1, le=100, description="每账号每日最大上传数")
    shuffle: bool = Field(default=False, description="是否随机打乱任务顺序")
    auto_start: bool = Field(default=False, description="是否自动启动调度")
    publish_scheduler_mode: PublishSchedulerMode = Field(
        default=PublishSchedulerMode.TASK,
        description="发布 scheduler 候选源模式：task=旧 ready task，pool=Creative publish pool",
    )
    publish_pool_kill_switch: bool = Field(default=False, description="开启后强制回退旧 task 路径")
    publish_pool_shadow_read: bool = Field(default=False, description="开启后记录 task 与 pool 候选差异")

    @field_validator("end_hour")
    @classmethod
    def end_hour_after_start(cls, v: int, info: Any) -> int:
        start = info.data.get("start_hour")
        if start is not None and v <= start:
            raise ValueError("end_hour 必须大于 start_hour")
        return v


class ScheduleConfigResponse(BaseModel):
    """调度配置响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_hour: int
    end_hour: int
    interval_minutes: int
    max_per_account_per_day: int
    shuffle: bool
    auto_start: bool
    publish_scheduler_mode: PublishSchedulerMode
    publish_pool_kill_switch: bool
    publish_pool_shadow_read: bool
    created_at: datetime
    updated_at: datetime


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
    scheduler_mode: PublishSchedulerMode = PublishSchedulerMode.TASK
    effective_scheduler_mode: PublishSchedulerMode = PublishSchedulerMode.TASK
    publish_pool_kill_switch: bool = False
    publish_pool_shadow_read: bool = False
    scheduler_shadow_diff: Optional[dict[str, Any]] = None


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


class BackupResponse(BaseModel):
    """备份响应"""
    success: bool
    backup_file: str


class SystemConfigResponse(BaseModel):
    """系统配置响应（真实 runtime-config + 只读系统信息）"""
    material_base_path: str = Field(
        ...,
        description="当前唯一支持运行时修改的设置项；优先读取 runtime-config，缺失时回退到 startup-env。",
    )
    auto_backup: bool = Field(
        ...,
        description="兼容占位字段；当前始终为 false，且不支持运行时修改。",
    )
    log_level: str = Field(
        ...,
        description="只读启动期配置；权威来源是 .env / backend/core/config.py，不支持运行时修改。",
    )


class SystemConfigUpdateResponse(BaseModel):
    """系统配置更新响应（仅 material_base_path 可真实写入）"""
    success: bool
    material_base_path: Optional[str] = Field(
        None,
        description="成功写入后的素材根目录；当前唯一支持运行时修改的设置项。",
    )
    auto_backup: Optional[bool] = Field(
        None,
        description="兼容占位字段；当前不会被写入，若请求传入将被明确拒绝。",
    )
    log_level: Optional[str] = Field(
        None,
        description="只读启动期配置回显；不会在运行时写回。",
    )


class MaterialStatsResponse(BaseModel):
    """素材统计响应"""
    videos: int
    copywritings: int
    covers: int
    audios: int
    topics: int
    products: int
    products_with_video: int
    coverage_rate: float


# ============ 预览 Schema ============

class PreviewCloseRequest(BaseModel):
    """关闭预览浏览器请求"""
    save_session: bool = False


class PreviewStatusResponse(BaseModel):
    """预览状态响应"""
    is_open: bool
    account_id: Optional[int] = None


class PreviewActionResponse(PreviewStatusResponse):
    """预览浏览器操作响应"""
    success: bool
    message: str


# ============ PublishProfile Schema ============

class CompositionMode(str, Enum):
    NONE = "none"
    COZE = "coze"
    LOCAL_FFMPEG = "local_ffmpeg"


class PublishProfileCreate(BaseModel):
    """创建合成配置档"""
    name: str = Field(..., min_length=1, max_length=128)
    is_default: bool = False
    composition_mode: CompositionMode = CompositionMode.NONE
    coze_workflow_id: Optional[str] = Field(None, max_length=128)
    composition_params: Optional[str] = Field(
        None,
        description="profile 级 opaque JSON 配置；Phase 6 结论为 keep-json。",
    )
    global_topic_ids: List[int] = Field(
        default_factory=list,
        description="profile-level default topics；当前由 publish_profile_topics 作为 canonical source，仍返回兼容 `topic_ids` shape。",
    )
    auto_retry: bool = True
    max_retry_count: int = Field(default=3, ge=0, le=10)

    @field_validator("composition_params")
    @classmethod
    def validate_composition_params(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                json.loads(v)
            except (ValueError, TypeError):
                raise ValueError("composition_params 必须是合法的 JSON 字符串")
        return v


class PublishProfileUpdate(BaseModel):
    """更新合成配置档"""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    is_default: Optional[bool] = None
    composition_mode: Optional[CompositionMode] = None
    coze_workflow_id: Optional[str] = Field(None, max_length=128)
    composition_params: Optional[str] = Field(
        None,
        description="profile 级 opaque JSON 配置；Phase 6 结论为 keep-json。",
    )
    global_topic_ids: Optional[List[int]] = Field(
        None,
        description="profile-level default topics；写入时会同步 relation rows 与 legacy JSON fallback。",
    )
    auto_retry: Optional[bool] = None
    max_retry_count: Optional[int] = Field(None, ge=0, le=10)

    @field_validator("composition_params")
    @classmethod
    def validate_composition_params(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                json.loads(v)
            except (ValueError, TypeError):
                raise ValueError("composition_params 必须是合法的 JSON 字符串")
        return v


class PublishProfileResponse(BaseModel):
    """合成配置档响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_default: bool
    composition_mode: CompositionMode
    coze_workflow_id: Optional[str] = None
    composition_params: Optional[str] = None
    global_topic_ids: List[int] = Field(
        default_factory=list,
        description="profile-level default topics；当前 TaskAssembler 会自动并入任务，canonical source 为 relation rows。",
    )
    auto_retry: bool
    max_retry_count: int
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _parse_global_topic_ids(cls, data: Any) -> Any:
        """将数据库中的 JSON 字符串解析为 List[int]。"""
        raw = (
            data.get("global_topic_ids") if isinstance(data, dict)
            else getattr(data, "global_topic_ids", None)
        )
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except (ValueError, TypeError):
                parsed = []
            if isinstance(data, dict):
                data["global_topic_ids"] = parsed
            else:
                data = {c.key: getattr(data, c.key) for c in data.__class__.__table__.columns}
                data["global_topic_ids"] = parsed
        return data


class PublishProfileListResponse(BaseModel):
    """合成配置档列表响应"""
    total: int
    items: List[PublishProfileResponse]


# ============ 话题组 Schema ============

class TopicGroupCreate(BaseModel):
    """创建话题组"""
    name: str = Field(..., min_length=1, max_length=128)
    topic_ids: List[int] = Field(default_factory=list, description="命名话题列表；canonical source 为 topic_group_topics，当前不会自动注入 task assembly")


class TopicGroupUpdate(BaseModel):
    """更新话题组"""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    topic_ids: Optional[List[int]] = Field(None, description="命名话题列表；写入时同步 relation rows 与 legacy JSON fallback，当前不会自动注入 task assembly")


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
    """设置全局话题请求（legacy singleton topic surface）"""
    topic_ids: List[int] = Field(..., description="legacy singleton topic surface；canonical source 为 global_topics，当前不会自动注入 task assembly")


class GlobalTopicResponse(BaseModel):
    """全局话题响应（legacy singleton topic surface）"""
    topic_ids: List[int] = Field(
        ...,
        description="当前读写 global_topics，并 dual-write PublishConfig.global_topic_ids 作为 fallback；不会自动注入 task assembly。",
    )
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
