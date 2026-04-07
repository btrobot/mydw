# 素材管理前端重构设计

> Version: 1.0.0 | Updated: 2026-04-07
> Owner: Tech Lead
> Status: Proposed (待用户审批)

---

## 1. 问题分析

当前 `Material.tsx` 是一个 1100 行的单文件，包含：

| 区域 | 内容 | 问题 |
|------|------|------|
| 顶部统计卡片 | 6 个 Statistic 卡片 | 占据视觉空间，非高频操作 |
| 商品管理 Card | 商品 CRUD 卡片列表 | 与素材 Tab 混在一起，定位不清 |
| 5 个 Tabs | 视频/文案/封面/音频/话题 | 所有素材类型挤在同一页面 |

核心矛盾：商品是素材的组织维度，不是素材本身；5 种素材类型功能独立，不需要同时展示。

---

## 2. 导航结构设计

将原来的单一「素材管理」菜单拆分为一个菜单组：

```
侧边栏导航
├── 数据看板
├── 账号管理
├── 任务管理
├── 素材中心 (SubMenu, 展开)          ← 新菜单组
│   ├── 素材总览                       ← 统计仪表盘 + 快捷入口
│   ├── 视频管理                       ← 原 VideoTab
│   ├── 文案管理                       ← 原 CopywritingTab
│   ├── 封面管理                       ← 原 CoverTab
│   ├── 音频管理                       ← 原 AudioTab
│   └── 话题管理                       ← 原 TopicTab
├── 商品管理                           ← 从素材页独立出来，升级为一级菜单
├── AI 剪辑
└── 系统设置
```

设计理由：
- 商品是素材的组织维度，与账号、任务同级，应作为独立一级菜单
- 5 种素材类型各自独立页面，减少单页面复杂度
- 「素材总览」提供统计和快捷导航，替代原来的统计卡片区域

---

## 3. 页面拆分方案

### 3.1 页面清单

| 页面 | 路由 | 类型 | 职责 |
|------|------|------|------|
| 素材总览 | `/material` | 仪表盘页 | 素材统计、各类素材数量、商品覆盖率、快捷操作入口 |
| 视频管理 | `/material/video` | 列表页 | 视频 CRUD、上传、扫描导入、按商品筛选 |
| 文案管理 | `/material/copywriting` | 列表页 | 文案 CRUD、批量导入、按商品筛选 |
| 封面管理 | `/material/cover` | 列表页 | 封面上传、列表、按视频筛选 |
| 音频管理 | `/material/audio` | 列表页 | 音频上传、列表 |
| 话题管理 | `/material/topic` | 列表页 | 话题 CRUD、得物搜索、全局话题设置 |
| 商品管理 | `/product` | 列表页 | 商品 CRUD、关联素材查看 |
| 商品详情 | `/product/:id` | 详情页 | 单个商品的关联视频、文案一览 |

### 3.2 各页面职责说明

#### 素材总览 (`/material`)

展示全局素材健康状态，帮助用户快速了解素材库现状。

```
┌─────────────────────────────────────────────────────┐
│  素材总览                                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│  │视频  │ │文案  │ │封面  │ │音频  │ │话题  │      │
│  │ 128  │ │ 256  │ │  64  │ │  12  │ │  45  │      │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘     │
│                                                     │
│  ┌──────────────┐                                   │
│  │ 商品覆盖率    │                                   │
│  │    85%       │                                   │
│  └──────────────┘                                   │
│                                                     │
│  快捷操作                                            │
│  [扫描导入视频]  [批量导入文案]  [搜索话题]           │
│                                                     │
│  最近添加                                            │
│  (最近 5 条视频/文案的简要列表)                       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### 视频管理 (`/material/video`) — 列表页模式

```
┌─────────────────────────────────────────────────────┐
│  视频管理                                            │
├─────────────────────────────────────────────────────┤
│  筛选栏                                              │
│  [商品筛选 ▼]  [状态筛选 ▼]  [关键词搜索...]        │
├─────────────────────────────────────────────────────┤
│  操作栏                                              │
│  [上传视频]  [扫描导入]  [手动添加]                   │
│  (选中时) [批量删除(3)]                              │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────┐    │
│  │  Table                                       │    │
│  │  名称 | 状态 | 商品 | 大小 | 时长 | 操作     │    │
│  │  ...                                         │    │
│  │                                              │    │
│  │  共 128 条          < 1 2 3 ... 13 >         │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

#### 商品管理 (`/product`) — 列表页模式

```
┌─────────────────────────────────────────────────────┐
│  商品管理                                            │
├─────────────────────────────────────────────────────┤
│  筛选栏                                              │
│  [名称搜索...]                                       │
├─────────────────────────────────────────────────────┤
│  操作栏                                              │
│  [添加商品]                                          │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────┐    │
│  │  Table                                       │    │
│  │  商品名 | 链接 | 视频数 | 文案数 | 操作      │    │
│  │  ...                                         │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

点击商品名称进入商品详情页。

#### 商品详情 (`/product/:id`) — 详情页模式

```
┌─────────────────────────────────────────────────────┐
│  ← 返回商品列表    商品详情: Nike Air Max 270         │
├─────────────────────────────────────────────────────┤
│  商品信息                                            │
│  名称: Nike Air Max 270                              │
│  链接: https://...                [编辑]             │
├─────────────────────────────────────────────────────┤
│  关联素材                                            │
│  ┌─ Tabs ──────────────────────────────────────┐    │
│  │ [关联视频(12)]  [关联文案(8)]                │    │
│  │                                              │    │
│  │  (对应素材的 Table，已按此商品筛选)            │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## 4. 页面布局模式

定义三种标准布局模式，所有页面遵循统一结构。

### 4.1 列表页模式 (ListPage)

适用于：视频管理、文案管理、封面管理、音频管理、话题管理、商品管理

```
┌─────────────────────────────────────┐
│  PageHeader (标题 + 面包屑)          │
├─────────────────────────────────────┤
│  FilterBar (筛选条件区)              │
│  Select / Input / DatePicker ...    │
├─────────────────────────────────────┤
│  ActionBar (操作按钮区)              │
│  [新增] [导入] [批量删除]            │
├─────────────────────────────────────┤
│  DataTable (数据表格)                │
│  columns + pagination + selection   │
├─────────────────────────────────────┤
│  Modal (新增/编辑弹窗，按需渲染)     │
└─────────────────────────────────────┘
```

布局规则：
- FilterBar 和 ActionBar 合并为一个 Card，筛选在左，操作按钮在右
- Table 独立 Card，带分页和行选择
- 新增/编辑使用 Modal，不跳转页面

### 4.2 详情页模式 (DetailPage)

适用于：商品详情

```
┌─────────────────────────────────────┐
│  PageHeader (返回按钮 + 标题)        │
├─────────────────────────────────────┤
│  DescriptionCard (基本信息)          │
│  Descriptions 组件展示字段           │
│                          [编辑按钮]  │
├─────────────────────────────────────┤
│  RelatedData (关联数据)              │
│  Tabs 切换不同关联列表               │
└─────────────────────────────────────┘
```

### 4.3 仪表盘模式 (DashboardPage)

适用于：素材总览

```
┌─────────────────────────────────────┐
│  PageHeader (标题)                   │
├─────────────────────────────────────┤
│  StatisticCards (统计卡片 Row)       │
│  Row > Col > Card > Statistic       │
├─────────────────────────────────────┤
│  QuickActions (快捷操作区)           │
│  Button 组，点击跳转到对应页面       │
├─────────────────────────────────────┤
│  RecentActivity (最近动态)           │
│  简要列表，最近添加的素材            │
└─────────────────────────────────────┘
```

---

## 5. 组件拆分方案

### 5.1 从 Material.tsx 拆出的组件

| 原始代码 | 新文件 | 类型 |
|----------|--------|------|
| `Material()` 主函数 (统计部分) | `pages/material/MaterialOverview.tsx` | 页面组件 |
| `VideoTab()` | `pages/material/VideoList.tsx` | 页面组件 |
| `CopywritingTab()` | `pages/material/CopywritingList.tsx` | 页面组件 |
| `CoverTab()` | `pages/material/CoverList.tsx` | 页面组件 |
| `AudioTab()` | `pages/material/AudioList.tsx` | 页面组件 |
| `TopicTab()` | `pages/material/TopicList.tsx` | 页面组件 |
| `ProductSection()` | `pages/product/ProductList.tsx` | 页面组件 |
| (新增) | `pages/product/ProductDetail.tsx` | 页面组件 |
| `formatSize()`, `formatDuration()` | `utils/format.ts` | 工具函数 |
| `handleApiError()` | `utils/error.ts` | 工具函数 |

### 5.2 新增共享组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `ListPageLayout` | `components/ListPageLayout.tsx` | 列表页通用布局（筛选栏 + 操作栏 + Table 容器） |
| `FilterBar` | `components/FilterBar.tsx` | 筛选条件栏（左侧筛选 + 右侧操作按钮） |
| `BatchDeleteButton` | `components/BatchDeleteButton.tsx` | 批量删除按钮（选中计数 + Popconfirm） |
| `ProductSelect` | `components/ProductSelect.tsx` | 商品选择器（多处复用：视频、文案筛选和表单） |

### 5.3 目录结构

```
frontend/src/
├── pages/
│   ├── material/                    ← 素材中心页面组
│   │   ├── MaterialOverview.tsx     ← 素材总览（仪表盘）
│   │   ├── VideoList.tsx            ← 视频管理（列表页）
│   │   ├── CopywritingList.tsx      ← 文案管理（列表页）
│   │   ├── CoverList.tsx            ← 封面管理（列表页）
│   │   ├── AudioList.tsx            ← 音频管理（列表页）
│   │   └── TopicList.tsx            ← 话题管理（列表页）
│   ├── product/                     ← 商品页面组
│   │   ├── ProductList.tsx          ← 商品列表（列表页）
│   │   └── ProductDetail.tsx        ← 商品详情（详情页）
│   ├── Dashboard.tsx
│   ├── Account.tsx
│   ├── Task.tsx
│   ├── Material.tsx                 ← 删除（功能已拆分）
│   ├── AIClip.tsx
│   └── Settings.tsx
├── components/
│   ├── Layout.tsx                   ← 更新导航菜单
│   ├── ListPageLayout.tsx           ← 新增
│   ├── FilterBar.tsx                ← 新增
│   ├── BatchDeleteButton.tsx        ← 新增
│   └── ProductSelect.tsx            ← 新增
└── utils/
    ├── format.ts                    ← 提取 formatSize, formatDuration
    └── error.ts                     ← 提取 handleApiError
```

---

## 6. 路由设计

### 6.1 路由表

```typescript
<Routes>
  <Route path="/" element={<Layout />}>
    <Route index element={<Navigate to="/dashboard" replace />} />
    <Route path="dashboard" element={<Dashboard />} />
    <Route path="account" element={<Account />} />
    <Route path="task" element={<Task />} />

    {/* 素材中心 */}
    <Route path="material" element={<MaterialOverview />} />
    <Route path="material/video" element={<VideoList />} />
    <Route path="material/copywriting" element={<CopywritingList />} />
    <Route path="material/cover" element={<CoverList />} />
    <Route path="material/audio" element={<AudioList />} />
    <Route path="material/topic" element={<TopicList />} />

    {/* 商品管理 */}
    <Route path="product" element={<ProductList />} />
    <Route path="product/:id" element={<ProductDetail />} />

    <Route path="ai-clip" element={<AIClip />} />
    <Route path="settings" element={<Settings />} />
  </Route>
</Routes>
```

### 6.2 导航菜单配置

```typescript
const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '数据看板' },
  { key: '/account', icon: <UserOutlined />, label: '账号管理' },
  { key: '/task', icon: <FileTextOutlined />, label: '任务管理' },
  {
    key: '/material',
    icon: <FolderOutlined />,
    label: '素材中心',
    children: [
      { key: '/material', label: '素材总览' },
      { key: '/material/video', label: '视频管理' },
      { key: '/material/copywriting', label: '文案管理' },
      { key: '/material/cover', label: '封面管理' },
      { key: '/material/audio', label: '音频管理' },
      { key: '/material/topic', label: '话题管理' },
    ],
  },
  { key: '/product', icon: <ShopOutlined />, label: '商品管理' },
  { key: '/ai-clip', icon: <ScissorOutlined />, label: 'AI 剪辑' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
]
```

注意：Ant Design Menu 的 SubMenu `key` 与子项 `key` 不能重复。素材总览的 key 需要特殊处理（如使用 `/material/overview` 或在 selectedKeys 逻辑中做精确匹配）。最终实现时建议：

```
素材总览路由: /material          (index route)
SubMenu key:  'material-group'   (不参与路由匹配)
```

---

## 7. 交互流程

### 7.1 素材管理主流程

```
用户打开应用
  → 侧边栏展开「素材中心」
  → 默认进入「素材总览」
  → 查看统计数据
  → 点击「视频管理」或快捷操作按钮
  → 进入视频列表页
  → 筛选/搜索/上传/删除
```

### 7.2 视频上传流程

```
用户进入「视频管理」
  → (可选) 选择「上传到商品」下拉框
  → 点击「上传视频」按钮
  → 选择本地 .mp4/.mov 文件
  → 上传完成，列表自动刷新
```

### 7.3 扫描导入流程

```
用户进入「视频管理」
  → 点击「扫描导入」按钮
  → 后端扫描 MATERIAL_BASE_PATH
  → 弹窗显示导入结果（新增/跳过/失败）
  → 列表自动刷新
```

### 7.4 商品 → 素材关联查看

```
用户进入「商品管理」
  → 查看商品列表（含关联视频数、文案数）
  → 点击商品名称
  → 进入商品详情页
  → 通过 Tabs 查看该商品关联的视频和文案
  → 可直接在详情页跳转到对应素材的管理页面（带商品筛选参数）
```

### 7.5 话题管理流程

```
用户进入「话题管理」
  → 搜索得物话题 → 添加到话题库
  → 设置全局话题（从话题库中选择）
  → 管理话题库（添加/删除/排序）
```

---

## 8. Layout.tsx 改动要点

当前 Layout 使用扁平 Menu items 数组。改动：

1. 引入 `SubMenu` 结构（Ant Design Menu 的 `children` 属性）
2. 处理 `selectedKeys` 逻辑：子路由高亮时父菜单自动展开
3. 处理 `openKeys` 状态：记住用户展开/折叠的菜单组
4. 商品管理新增为一级菜单项

```typescript
// selectedKeys 匹配逻辑
const selectedKey = menuItems
  .flatMap(item => item.children ? item.children : [item])
  .find(item => location.pathname === item.key || location.pathname.startsWith(item.key + '/'))
  ?.key ?? location.pathname
```

---

## 9. 后端 API 兼容性

本次重构不修改后端 API。所有现有 hooks 和 API 调用保持不变：

| 页面 | 使用的 hooks | API 端点 |
|------|-------------|---------|
| VideoList | `useVideos`, `useCreateVideo`, `useDeleteVideo`, `useUploadVideo`, `useScanVideos`, `useBatchDeleteVideos` | `/api/videos/*` |
| CopywritingList | `useCopywritings`, `useCreateCopywriting`, `useDeleteCopywriting`, `useUpdateCopywriting`, `useImportCopywritings`, `useBatchDeleteCopywritings` | `/api/copywritings/*` |
| CoverList | `useCovers`, `useUploadCover`, `useDeleteCover`, `useBatchDeleteCovers` | `/api/covers/*` |
| AudioList | `useAudios`, `useUploadAudio`, `useDeleteAudio`, `useBatchDeleteAudios` | `/api/audios/*` |
| TopicList | `useTopics`, `useCreateTopic`, `useDeleteTopic`, `useSearchTopics`, `useGlobalTopics`, `useSetGlobalTopics`, `useBatchDeleteTopics` | `/api/topics/*` |
| ProductList | `useProductsV2`, `useCreateProductV2`, `useDeleteProductV2`, `useUpdateProductV2` | `/api/products/*` |
| MaterialOverview | `useQuery(['material-stats'])` | `/api/system/material-stats` |
| ProductDetail | `useProductsV2` (单个) + `useVideos(productId)` + `useCopywritings(productId)` | 复用现有端点 |

唯一新增需求：商品详情页需要按 `product_id` 查询关联素材，现有 API 已支持 `?product_id=` 参数。

---

## 10. 实施计划

### Phase 1: 基础拆分（无功能变更）

1. 创建 `pages/material/` 和 `pages/product/` 目录
2. 将 Material.tsx 中的各 Tab 组件提取为独立页面文件
3. 提取 `formatSize`, `formatDuration`, `handleApiError` 到 utils
4. 更新路由配置
5. 更新 Layout 导航菜单

验收标准：所有页面功能与重构前完全一致，只是分布在不同路由。

### Phase 2: 布局优化

1. 实现 `ListPageLayout` 共享组件
2. 各列表页统一使用 ListPageLayout
3. 实现 `ProductSelect` 共享组件
4. 实现素材总览仪表盘页

### Phase 3: 商品详情页

1. 实现 `ProductDetail` 详情页
2. 商品列表页增加关联素材计数列
3. 商品详情页展示关联视频和文案

---

## 11. 架构审查清单

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 解决实际问题 | OK | 拆分 1100 行单文件为 8 个独立页面，解决拥挤问题 |
| 最简方案 | OK | 纯前端重构，不改后端 API，不引入新依赖 |
| 过度设计 | OK | 只新增 4 个共享组件，均有 2+ 处复用 |
| 可删除性 | OK | 每个页面独立，删除任一页面不影响其他 |
| 数据一致性 | OK | 复用现有 React Query hooks，缓存策略不变 |
| 可理解性 | OK | 一个文件一个页面，职责清晰 |
| 可测试性 | OK | 页面独立后可单独编写 E2E 测试 |
| 安全性 | N/A | 纯 UI 重构，无安全变更 |
