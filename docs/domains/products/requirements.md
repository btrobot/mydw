# 商品（Product）需求文档

> Version: 1.0.0 | Updated: 2026-04-07
> Owner: Tech Lead
> Status: Draft

---

## 1. 业务背景

### 1.1 商品的重新定义

在 DewuGoJin 系统中，"商品"不是传统电商意义上的可售卖商品，而是：

**商品 = 得物平台的一个推荐商品 = 素材的包裹 = 添加素材的快捷方式**

每个商品对应得物平台上的一个商品页面，核心价值在于：从商品的得物页面链接中，可以自动解析出一组发布所需的素材（视频、封面、文案、话题）。

### 1.2 核心概念

```
商品 (Product)
  ├── 商品说明 (description)
  ├── 得物页面链接 (dewu_url)
  └── 素材包 (从 dewu_url 解析)
        ├── 封面图 (Cover)
        ├── 视频 (Video)
        ├── 标题/文案 (Copywriting)
        └── 话题列表 (Topic[])
```

### 1.3 业务流程

```
用户添加商品 (填写 dewu_url)
       │
       ▼
系统访问 dewu_url (Patchright 浏览器)
       │
       ▼
解析页面内容 → 提取素材包
       │
       ▼
自动创建素材记录 (Video, Cover, Copywriting, Topic)
       │
       ▼
自动关联商品与素材
       │
       ▼
用户基于商品素材创建发布任务
```

---

## 2. 素材包数据结构

从得物商品页面解析出的素材包定义：

```python
class MaterialPack:
    """从得物页面解析出的素材包"""
    cover_urls: List[str]       # 封面图片 URL 列表
    video_url: Optional[str]    # 视频 URL（可能不存在）
    title: str                  # 标题（用作文案）
    topics: List[str]           # 话题名称列表
```

### 2.1 字段说明

| 字段 | 来源 | 说明 |
|------|------|------|
| cover_urls | 页面商品图片 | 可能有多张，取第一张作为主封面 |
| video_url | 页面视频元素 | 部分商品页无视频，此字段可为空 |
| title | 页面标题/商品名 | 用作发布文案的内容 |
| topics | 页面话题标签 | 如 #得物开箱 #好物推荐 等 |

### 2.2 素材包与现有模型的映射

| 素材包字段 | 目标模型 | 映射方式 |
|-----------|---------|---------|
| cover_urls[0] | Cover | 下载图片到本地，创建 Cover 记录 |
| video_url | Video | 下载视频到本地，创建 Video 记录（product_id 关联） |
| title | Copywriting | 创建 Copywriting 记录（product_id 关联，source_type="dewu_parse"） |
| topics[] | Topic | 查找或创建 Topic 记录（source="dewu_parse"） |

---

## 3. 功能需求

### 3.1 商品 CRUD（已有）

现有功能，无需修改：

| 操作 | 端点 | 状态 |
|------|------|------|
| 创建商品 | POST /api/products | 已实现 |
| 商品列表 | GET /api/products | 已实现 |
| 商品详情 | GET /api/products/{id} | 已实现 |
| 更新商品 | PUT /api/products/{id} | 已实现 |
| 删除商品 | DELETE /api/products/{id} | 已实现（含引用检查） |

### 3.2 新功能：从得物链接解析素材包

#### 3.2.1 触发方式

用户对一个已有商品（必须有 dewu_url）发起"解析素材"操作。

#### 3.2.2 解析流程

```
POST /api/products/{id}/parse-materials
       │
       ▼
  ┌─────────────────────────────┐
  │ 1. 校验商品存在且有 dewu_url │
  └──────────┬──────────────────┘
             │
             ▼
  ┌─────────────────────────────┐
  │ 2. 用 Patchright 打开页面    │
  │    (需要一个已登录的账号)     │
  └──────────┬──────────────────┘
             │
             ▼
  ┌─────────────────────────────┐
  │ 3. 等待页面加载完成          │
  │    提取: 图片/视频/标题/话题  │
  └──────────┬──────────────────┘
             │
             ▼
  ┌─────────────────────────────┐
  │ 4. 下载媒体文件到本地        │
  │    (封面图、视频)            │
  └──────────┬──────────────────┘
             │
             ▼
  ┌─────────────────────────────┐
  │ 5. 创建素材记录并关联商品    │
  │    Video, Cover, Copywriting │
  │    Topic (查找或创建)        │
  └──────────┬──────────────────┘
             │
             ▼
  ┌─────────────────────────────┐
  │ 6. 返回解析结果              │
  └─────────────────────────────┘
```

#### 3.2.3 解析结果响应

```python
class ParseMaterialsResponse:
    success: bool
    product_id: int
    video: Optional[VideoResponse]          # 创建的视频记录
    covers: List[CoverResponse]             # 创建的封面记录
    copywriting: Optional[CopywritingResponse]  # 创建的文案记录
    topics: List[TopicResponse]             # 关联的话题记录
    errors: List[str]                       # 部分失败时的错误信息
```

#### 3.2.4 幂等性设计

重复解析同一商品时的行为：

| 素材类型 | 策略 |
|---------|------|
| Video | 如果商品已有关联视频，跳过（不重复下载） |
| Cover | 如果已有封面，跳过 |
| Copywriting | 如果商品已有关联文案，跳过 |
| Topic | 按名称去重，已存在的 Topic 直接复用 |

---

## 4. 数据模型影响

### 4.1 现有模型（无需修改）

当前 Product 模型已具备所需字段：

```python
class Product(Base):
    id          # PK
    name        # 商品名称
    link        # 通用链接（保留）
    description # 商品说明
    dewu_url    # 得物页面链接 -- 解析入口
    image_url   # 商品图片（可存解析出的封面 URL）
```

现有关系已支持：
- Product 1:N Video（通过 `videos.product_id`）
- Product 1:N Copywriting（通过 `copywritings.product_id`）

### 4.2 需要新增的关联

当前缺失的关系：

| 关系 | 现状 | 需要 |
|------|------|------|
| Product - Topic | 无直接关联 | 新增 `product_topics` 关联表 |
| Product - Cover | 无直接关联（Cover 通过 Video 间接关联） | 可通过 Video 间接关联，暂不新增 |

#### 4.2.1 新增 ProductTopic 关联表

```python
class ProductTopic(Base):
    """商品-话题关联表"""
    __tablename__ = "product_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint('product_id', 'topic_id'),)
```

#### 4.2.2 Product 模型新增关系

```python
class Product(Base):
    # ... 现有字段不变 ...

    # 新增关系
    topics = relationship("Topic", secondary="product_topics", passive_deletes=True)
```

#### 4.2.3 迁移脚本

需要新增迁移 `009_product_topics.py`：
- 创建 `product_topics` 表
- 添加唯一约束 (product_id, topic_id)

### 4.3 ER 图（更新后）

```
accounts 1──N tasks N──1 products
                │              │
                │         1──N videos 1──N covers
                │              │
                │         1──N copywritings
                │              │
                │         N──N topics (via product_topics)  ← 新增
                │
                ├──N publish_logs
                │
                └──N task_topics N──1 topics
```

---

## 5. API 设计

### 5.1 新增端点

#### POST /api/products/{id}/parse-materials

从商品的 dewu_url 解析素材包，自动创建素材记录。

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | int (path) | 是 | 商品 ID |
| account_id | int (query) | 否 | 指定用于浏览的账号 ID（需已登录），不传则自动选择 |

**成功响应** (200):

```json
{
  "success": true,
  "product_id": 1,
  "video": { "id": 10, "name": "...", "file_path": "..." },
  "covers": [{ "id": 5, "file_path": "..." }],
  "copywriting": { "id": 8, "content": "..." },
  "topics": [{ "id": 3, "name": "得物开箱" }],
  "errors": []
}
```

**错误响应**:

| 状态码 | 场景 |
|--------|------|
| 404 | 商品不存在 |
| 400 | 商品无 dewu_url |
| 400 | 无可用的已登录账号 |
| 500 | 页面解析失败 |

### 5.2 现有端点增强

#### GET /api/products/{id} -- 响应增加关联素材摘要

在 ProductResponse 中增加可选的素材统计字段：

```python
class ProductResponse(ProductBase):
    # ... 现有字段 ...
    video_count: int = 0          # 关联视频数
    copywriting_count: int = 0    # 关联文案数
    topic_ids: List[int] = []     # 关联话题 ID 列表
```

---

## 6. 解析流程设计

### 6.1 技术方案

使用 Patchright（已有 `core/dewu_client.py`）访问得物商品页面，通过 DOM 解析提取素材。

### 6.2 DewuClient 扩展

在 `DewuClient` 中新增方法：

```python
async def parse_product_page(self, dewu_url: str) -> MaterialPack:
    """
    访问得物商品页面，解析素材包。

    流程:
    1. page.goto(dewu_url)
    2. 等待页面关键元素加载
    3. 提取图片 URL、视频 URL、标题、话题
    4. 返回 MaterialPack
    """
```

### 6.3 媒体文件下载

解析出 URL 后，需要将媒体文件下载到本地：

```
data/
  materials/
    videos/      # 下载的视频文件
    covers/      # 下载的封面图片
```

下载使用 httpx 异步客户端，遵循现有 async 规范。

### 6.4 服务层

新增 `services/product_parse_service.py`：

```python
class ProductParseService:
    """商品素材解析服务"""

    async def parse_and_create_materials(
        self,
        db: AsyncSession,
        product: Product,
        account_id: Optional[int] = None,
    ) -> ParseMaterialsResponse:
        """
        完整的解析流程:
        1. 选择可用账号（已登录）
        2. 用 DewuClient 解析页面
        3. 下载媒体文件
        4. 创建素材记录
        5. 关联商品与素材
        """
```

### 6.5 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 页面加载超时 | 返回错误，建议重试 |
| 页面结构变化（选择器失效） | 记录日志，返回部分结果 |
| 视频下载失败 | 跳过视频，继续处理其他素材 |
| 封面下载失败 | 跳过封面，继续处理其他素材 |
| 账号未登录 | 返回 400，提示先登录账号 |

设计原则：部分失败不阻塞整体流程，通过 `errors` 字段返回失败详情。

### 6.6 耗时预估

| 步骤 | 预估耗时 |
|------|---------|
| 打开页面并加载 | 5-15 秒 |
| DOM 解析 | < 1 秒 |
| 下载封面图 | 2-5 秒 |
| 下载视频 | 10-60 秒（取决于视频大小） |
| 创建 DB 记录 | < 1 秒 |
| 总计 | 20-80 秒 |

由于耗时较长，前端应使用 loading 状态提示用户等待。后续可考虑改为异步任务 + SSE 推送进度。

---

## 7. 待决策项

以下问题需要产品决策：

| 编号 | 问题 | 选项 | 建议 |
|------|------|------|------|
| D-1 | 解析操作是同步返回还是异步任务？ | 同步等待，非登录方式（不需要账号 cookie） |
| D-2 | 重复解析同一商品时已有素材怎么处理？ | 每次覆盖更新（页面内容可能变化） |
| D-3 | 是否支持批量解析？ | 先不做，MVP 仅单个 |
| D-4 | 商品删除时是否级联删除素材？ | 只删商品记录，素材保留 |

---

## 8. 实现优先级

| 阶段 | 内容 | 依赖 |
|------|------|------|
| P0 | ProductTopic 关联表 + 迁移脚本 | 无 |
| P0 | DewuClient.parse_product_page() | Patchright 环境 |
| P0 | ProductParseService | DewuClient 扩展 |
| P0 | POST /api/products/{id}/parse-materials | Service 层 |
| P1 | ProductResponse 增加素材统计 | 关联表就绪 |
| P1 | 前端"解析素材"按钮和交互 | API 就绪 |
| P2 | 异步解析 + SSE 进度推送 | 同步版本验证后 |
| P2 | 批量解析 | 单个解析稳定后 |
