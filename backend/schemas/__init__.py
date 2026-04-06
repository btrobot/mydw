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


class MaterialType(str, Enum):
    VIDEO = "video"
    TEXT = "text"
    COVER = "cover"
    TOPIC = "topic"
    AUDIO = "audio"


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

class TaskBase(BaseModel):
    video_path: Optional[str] = None
    content: Optional[str] = None
    topic: Optional[str] = None
    cover_path: Optional[str] = None


class TaskCreate(TaskBase):
    """创建任务"""
    account_id: int
    product_id: Optional[int] = None
    material_id: Optional[int] = None


class TaskUpdate(BaseModel):
    """更新任务"""
    video_path: Optional[str] = None
    content: Optional[str] = None
    topic: Optional[str] = None
    cover_path: Optional[str] = None
    account_id: Optional[int] = None
    product_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = None


class TaskResponse(TaskBase):
    """任务响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    product_id: Optional[int] = None
    status: TaskStatus
    publish_time: Optional[datetime] = None
    error_msg: Optional[str] = None
    priority: int
    created_at: datetime
    updated_at: datetime


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


# ============ 素材 Schema ============

class MaterialBase(BaseModel):
    type: MaterialType
    name: Optional[str] = None


class MaterialCreate(MaterialBase):
    """创建素材"""
    path: Optional[str] = None
    content: Optional[str] = None


class MaterialUpdate(BaseModel):
    """更新素材"""
    name: Optional[str] = None
    path: Optional[str] = None
    content: Optional[str] = None


class MaterialResponse(MaterialBase):
    """素材响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    path: Optional[str] = None
    content: Optional[str] = None
    size: Optional[int] = None
    duration: Optional[int] = None
    created_at: datetime


class MaterialListResponse(BaseModel):
    """素材列表响应"""
    total: int
    items: List[MaterialResponse]


# ============ 商品 Schema ============

class ProductBase(BaseModel):
    name: str
    link: Optional[str] = None


class ProductCreate(ProductBase):
    """创建商品"""
    pass


class ProductUpdate(BaseModel):
    """更新商品"""
    name: Optional[str] = None
    link: Optional[str] = None


class ProductResponse(ProductBase):
    """商品响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: Optional[str] = None
    created_at: datetime


class ProductListResponse(BaseModel):
    """商品列表响应"""
    total: int
    items: List[ProductResponse]


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
    total_materials: int


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


# ============ 通用响应 ============

class ApiResponse(BaseModel):
    """通用 API 响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[dict] = None
