"""
得物掘金工具 - Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============ 枚举定义 ============

class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


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
    pass


class AccountUpdate(BaseModel):
    """更新账号"""
    account_name: Optional[str] = None
    status: Optional[AccountStatus] = None
    cookie: Optional[str] = None


class AccountResponse(AccountBase):
    """账号响应"""
    id: int
    status: AccountStatus
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccountLoginRequest(BaseModel):
    """账号登录请求"""
    account_id: str


class AccountTestRequest(BaseModel):
    """账号测试请求"""
    account_id: int


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
    id: int
    account_id: int
    product_id: Optional[int] = None
    status: TaskStatus
    publish_time: Optional[datetime] = None
    error_msg: Optional[str] = None
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
    id: int
    path: Optional[str] = None
    content: Optional[str] = None
    size: Optional[int] = None
    duration: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


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
    id: int
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


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
    id: int
    name: str
    interval_minutes: int
    start_hour: int
    end_hour: int
    max_per_account_per_day: int
    shuffle: bool
    auto_start: bool

    class Config:
        from_attributes = True


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
    id: int
    level: str
    module: Optional[str] = None
    message: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SystemLogListResponse(BaseModel):
    """系统日志列表响应"""
    total: int
    items: List[SystemLogResponse]


class BackupRequest(BaseModel):
    """备份请求"""
    include_logs: bool = False


# ============ 通用响应 ============

class ApiResponse(BaseModel):
    """通用 API 响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[dict] = None
