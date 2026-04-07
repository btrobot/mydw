# 素材总览

> Layout Template: T6 Dashboard
> Route: `/material/overview`（`/material` 重定向至此）
> API: `GET /api/system/material-stats`
> Permissions: 无（当前未实现权限控制）

## 1. StatCards（6 卡片）

布局：`Row` gutter=16，每卡片 `Col` span=4（等宽六列）。

| # | Title | Field | Icon | Render | Click Navigate |
|---|-------|-------|------|--------|----------------|
| 1 | 视频 | `videos` | `VideoCameraOutlined` | 整数 | `/material/video` |
| 2 | 文案 | `copywritings` | `FileTextOutlined` | 整数 | `/material/copywriting` |
| 3 | 封面 | `covers` | `PictureOutlined` | 整数 | `/material/cover` |
| 4 | 音频 | `audios` | `SoundOutlined` | 整数 | `/material/audio` |
| 5 | 话题 | `topics` | `TagsOutlined` | 整数 | `/material/topic` |
| 6 | 商品覆盖率 | `coverage_rate` | `ShopOutlined` | `value * 100`，suffix="%"，precision=0 | `/product` |

卡片配置：
- `Card` size="small"，cursor: pointer
- 内部使用 `Statistic` 组件，prefix 为对应 Icon

## 2. QuickActions（6 按钮）

容器：`Card` title="快捷操作" size="small"，内部 `Space` wrap。

| # | Label | Navigate |
|---|-------|----------|
| 1 | 视频管理 | `/material/video` |
| 2 | 文案管理 | `/material/copywriting` |
| 3 | 封面管理 | `/material/cover` |
| 4 | 音频管理 | `/material/audio` |
| 5 | 话题管理 | `/material/topic` |
| 6 | 商品管理 | `/product` |

按钮类型：默认 `Button`（无 type 属性，即 default 样式）。

## 3. 数据获取

| Hook | queryKey | queryFn | 返回类型 |
|------|----------|---------|----------|
| `useQuery<MaterialStats>` | `['material-stats']` | `api.get('/system/material-stats')` | `MaterialStats` |

### MaterialStats 接口

```typescript
interface MaterialStats {
  videos: number
  copywritings: number
  covers: number
  audios: number
  topics: number
  coverage_rate: number   // 0~1 浮点数，前端 *100 显示
}
```

## 4. 交互流程

### 4.1 页面加载
1. 组件挂载 → `useQuery` 发起 `GET /api/system/material-stats`
2. 数据返回前，StatCards 显示 `0`（`stats?.field ?? 0` 兜底）
3. 数据返回后，StatCards 更新为实际值

### 4.2 卡片点击
1. 用户点击任一 StatCard → `navigate(target)` 跳转至对应管理页

### 4.3 快捷操作
1. 用户点击任一 QuickAction 按钮 → `navigate(target)` 跳转至对应管理页

---

## Issues

| # | Severity | Description |
|---|----------|-------------|
| 1 | Suggestion | `MaterialStats` 接口缺少后端返回的 `products` 和 `products_with_video` 字段。当前不影响功能，但接口定义与后端响应不完全对齐。 |
| 2 | Suggestion | StatCards 使用 inline style `cursor: 'pointer'`，建议提取为 CSS class 或 token 以保持一致性。 |
| 3 | Suggestion | 页面标题使用 inline style `marginTop: 0, marginBottom: 16`，建议统一为 CSS class。 |

---

## Hard Check

| 指标 | 数量 |
|------|------|
| StatCards | 6 |
| QuickAction buttons | 6 |
| API queries | 1（`GET /api/system/material-stats`） |
| Modals | 0 |
| Forms | 0 |
| Tables | 0 |
