# Dewu `__NEXT_DATA__` 解析 Schema（community-share 样例）

> 来源：用户提供的得物页面 HTML 片段  
> 节点：`<script id="__NEXT_DATA__" type="application/json">...`  
> 场景：`/community/community-share`  
> 生成时间：2026-04-18

## 1. 文档目标

这份文档说明得物分享页 `__NEXT_DATA__` JSON 的：

- 顶层结构
- 关键字段路径
- 面向业务抽取的子 schema
- 基于当前样本的真实字段示例
- 解析时的推荐规则与注意事项

当前样本属于**社区分享 / 视频动态**页面，核心业务数据集中在：

```text
props.pageProps.metaOGInfo.data[0]
```

其中真正的内容主体位于：

```text
props.pageProps.metaOGInfo.data[0].content
```

---

## 2. 顶层 Schema 概览

```text
__NEXT_DATA__
├── props
│   └── pageProps
│       ├── metaOGInfo
│       │   ├── code
│       │   ├── status
│       │   ├── msg
│       │   ├── data[]
│       │   │   └── item
│       │   │       ├── content
│       │   │       │   ├── content
│       │   │       │   ├── contentId
│       │   │       │   ├── contentType
│       │   │       │   ├── cover
│       │   │       │   ├── media
│       │   │       │   ├── title
│       │   │       │   └── videoShareUrl
│       │   │       └── userInfo
│       │   │           ├── icon
│       │   │           ├── userName
│       │   │           └── vIcon
│       │   ├── timestamp
│       │   └── traceId
│       ├── frontAbTestConfig
│       ├── trendId
│       ├── shareId
│       ├── source
│       ├── shareType
│       ├── isScreenShot
│       ├── shareChannel
│       ├── isPC
│       ├── routeQuery
│       ├── pageLink
│       ├── requestCostTime
│       ├── isSsr
│       ├── isCdn
│       ├── isInApp
│       └── osInfo
├── page
├── query
├── buildId
├── assetPrefix
├── isFallback
├── customServer
├── gip
├── appGip
└── scriptLoader
```

---

## 3. TypeScript 风格 Schema

### 3.1 顶层最小可用 schema

```ts
interface DewuNextDataRoot {
  props?: {
    pageProps?: {
      metaOGInfo?: DewuMetaOGInfo
      trendId?: string
      shareId?: string
      source?: string
      shareType?: string
      isScreenShot?: string
      shareChannel?: string
      isPC?: boolean
      routeQuery?: Record<string, string>
      pageLink?: string
      requestCostTime?: number
      isSsr?: boolean
      isCdn?: boolean
      isInApp?: boolean
      osInfo?: DewuOsInfo
      frontAbTestConfig?: unknown
    }
  }
  page?: string
  query?: Record<string, string>
  buildId?: string
  assetPrefix?: string
  isFallback?: boolean
  customServer?: boolean
  gip?: boolean
  appGip?: boolean
  scriptLoader?: unknown[]
}
```

### 3.2 `metaOGInfo` schema

```ts
interface DewuMetaOGInfo {
  code?: number
  status?: number
  msg?: string
  data?: DewuMetaOGItem[]
  timestamp?: number
  traceId?: string
}

interface DewuMetaOGItem {
  content?: DewuCommunityContent
  userInfo?: DewuUserInfo
}
```

### 3.3 内容主体 schema

```ts
interface DewuCommunityContent {
  content?: string              // 话题 / 文案串，如 "#tag1 #tag2 ..."
  contentId?: number            // 动态 ID
  contentType?: number          // 内容类型，样本中为 1
  cover?: DewuMediaAsset        // 主封面
  media?: {
    list?: DewuMediaAsset[]
  }
  title?: string                // 标题
  videoShareUrl?: string        // 带水印视频 URL（备选）
}

interface DewuMediaAsset {
  mediaType?: 'video' | 'img' | 'blur' | string
  url?: string
}

interface DewuUserInfo {
  icon?: string
  userName?: string
  vIcon?: string
}

interface DewuOsInfo {
  userAgent?: string
  osName?: string
  version?: string
  sVersion?: number
  isInApp?: boolean
  appVersion?: string
}
```

---

## 4. 当前样本的真实字段示例

### 4.1 页面级字段示例

| 路径 | 示例值 | 含义 |
|---|---|---|
| `props.pageProps.trendId` | `"303342107"` | 动态 ID |
| `props.pageProps.shareId` | `"7EYGAmy"` | 分享 ID |
| `props.pageProps.source` | `"videoTrend"` | 页面来源类型 |
| `props.pageProps.isPC` | `true` | 当前是否 PC UA |
| `props.pageProps.pageLink` | `https://m.dewu.com/h5-sociality/community/community-share?...` | 当前页面完整链接 |
| `page` | `"/community/community-share"` | Next.js page 路由 |
| `buildId` | `"tovfgBNIT9pwYr-Wrc5mv"` | Next build ID |
| `assetPrefix` | `"//h5static.dewu.com/h5-sociality/out"` | 静态资源前缀 |

### 4.2 `metaOGInfo` 字段示例

| 路径 | 示例值 | 含义 |
|---|---|---|
| `metaOGInfo.code` | `200` | 接口业务码 |
| `metaOGInfo.status` | `200` | 状态码 |
| `metaOGInfo.msg` | `"成功"` | 提示消息 |
| `metaOGInfo.timestamp` | `1776516561465` | 服务端时间戳 |
| `metaOGInfo.traceId` | `"0aee0e2969e37dd14aca7176c4a6f25f"` | 请求追踪 ID |

### 4.3 内容主体字段示例

样本路径：

```text
props.pageProps.metaOGInfo.data[0].content
```

实际示例：

```json
{
  "content": "#nike白橙 #经典AirForce #空军一号白橙 #nike空军一号白金款 #高颜值NIKE空军一号 ",
  "contentId": 303342107,
  "contentType": 1,
  "cover": {
    "mediaType": "img",
    "url": "https://image-cdn.dewu.com/app/2025/community/1386306438_byte1182245byte_cff1eba7af247820c4bab2c9b1fc202b_iOS_w1080h1438.jpg"
  },
  "media": {
    "list": [
      {
        "mediaType": "video",
        "url": "https://videocdn.poizon.com/app/mf/dw264_720p/526f727c-3580-403e-8dd3-7a1bc978ac75/_dur33233dur_43005a15018a9103f468cbb10e712f80_iOS_w1080h1920.mp4"
      },
      {
        "mediaType": "img",
        "url": "https://image-cdn.poizon.com/app/2025/community/1386306438_byte1182245byte_cff1eba7af247820c4bab2c9b1fc202b_iOS_w1080h1438.jpg"
      },
      {
        "mediaType": "blur",
        "url": "https://image-cdn.poizon.com/app/2025/community/1386306438_byte1182245byte_cff1eba7af247820c4bab2c9b1fc202b_iOS_w1080h1438.jpg?x-oss-process=image/blur,r_50,s_50|image/resize,h_480"
      }
    ]
  },
  "title": "空军一号 新款爱了爱了",
  "videoShareUrl": "https://videocdn.poizon.com/algorithm/wm/watermark_6d635b60-1b4d-11f0-a104-00163e361f29__dur33233dur_43005a15018a9103f468cbb10e712f80_iOS_w1080h1920.mp4"
}
```

### 4.4 作者字段示例

路径：

```text
props.pageProps.metaOGInfo.data[0].userInfo
```

示例：

```json
{
  "icon": "https://image-cdn.poizon.com/app/2025/other/1386306438_byte132211byte_59a94be79c6fcf5c547afec52f385d18_iOS_w1290h1290.jpg",
  "userName": "关你西红柿什么",
  "vIcon": ""
}
```

---

## 5. 面向业务抽取的目标 schema

如果目标是“从得物页面抽取可落库素材”，推荐收敛成下面这个业务对象：

```ts
interface ParsedDewuMaterialPack {
  trendId?: string
  shareId?: string
  pageLink?: string

  title?: string
  rawContent?: string
  topics: string[]

  primaryCoverUrl?: string
  imageUrls: string[]

  primaryVideoUrl?: string
  fallbackVideoUrl?: string

  authorName?: string
  authorAvatarUrl?: string
}
```

对应当前样本可解析为：

```json
{
  "trendId": "303342107",
  "shareId": "7EYGAmy",
  "pageLink": "https://m.dewu.com/h5-sociality/community/community-share?trendId=303342107&shareId=7EYGAmy&source=videoTrend&shareType=0&isScreenShot=0&shareChannel=6",
  "title": "空军一号 新款爱了爱了",
  "rawContent": "#nike白橙 #经典AirForce #空军一号白橙 #nike空军一号白金款 #高颜值NIKE空军一号 ",
  "topics": [
    "nike白橙",
    "经典AirForce",
    "空军一号白橙",
    "nike空军一号白金款",
    "高颜值NIKE空军一号"
  ],
  "primaryCoverUrl": "https://image-cdn.dewu.com/app/2025/community/1386306438_byte1182245byte_cff1eba7af247820c4bab2c9b1fc202b_iOS_w1080h1438.jpg",
  "imageUrls": [
    "https://image-cdn.dewu.com/app/2025/community/1386306438_byte1182245byte_cff1eba7af247820c4bab2c9b1fc202b_iOS_w1080h1438.jpg",
    "https://image-cdn.poizon.com/app/2025/community/1386306438_byte1182245byte_cff1eba7af247820c4bab2c9b1fc202b_iOS_w1080h1438.jpg"
  ],
  "primaryVideoUrl": "https://videocdn.poizon.com/app/mf/dw264_720p/526f727c-3580-403e-8dd3-7a1bc978ac75/_dur33233dur_43005a15018a9103f468cbb10e712f80_iOS_w1080h1920.mp4",
  "fallbackVideoUrl": "https://videocdn.poizon.com/algorithm/wm/watermark_6d635b60-1b4d-11f0-a104-00163e361f29__dur33233dur_43005a15018a9103f468cbb10e712f80_iOS_w1080h1920.mp4",
  "authorName": "关你西红柿什么",
  "authorAvatarUrl": "https://image-cdn.poizon.com/app/2025/other/1386306438_byte132211byte_59a94be79c6fcf5c547afec52f385d18_iOS_w1290h1290.jpg"
}
```

---

## 6. 字段解析规则建议

### 6.1 标题

优先路径：

```text
props.pageProps.metaOGInfo.data[0].content.title
```

当前样本：

```text
空军一号 新款爱了爱了
```

用途建议：

- `Product.name`
- `Copywriting.content` 的默认标题部分

### 6.2 话题

原始字段：

```text
props.pageProps.metaOGInfo.data[0].content.content
```

当前样本：

```text
#nike白橙 #经典AirForce #空军一号白橙 #nike空军一号白金款 #高颜值NIKE空军一号
```

推荐解析规则：

1. trim 首尾空白
2. 按 `#` 切分
3. 去掉空串
4. 对每个 tag 再 trim
5. 保留原始大小写

示例结果：

```json
[
  "nike白橙",
  "经典AirForce",
  "空军一号白橙",
  "nike空军一号白金款",
  "高颜值NIKE空军一号"
]
```

### 6.3 视频

优先路径：

```text
props.pageProps.metaOGInfo.data[0].content.media.list[].url
where mediaType == "video"
```

当前样本值：

```text
https://videocdn.poizon.com/app/mf/dw264_720p/526f727c-3580-403e-8dd3-7a1bc978ac75/_dur33233dur_43005a15018a9103f468cbb10e712f80_iOS_w1080h1920.mp4
```

备选路径：

```text
props.pageProps.metaOGInfo.data[0].content.videoShareUrl
```

当前样本值：

```text
https://videocdn.poizon.com/algorithm/wm/watermark_6d635b60-1b4d-11f0-a104-00163e361f29__dur33233dur_43005a15018a9103f468cbb10e712f80_iOS_w1080h1920.mp4
```

建议：

- 优先使用 `media.list[video]`
- `videoShareUrl` 仅作为降级路径
- 如果两者都存在，建议标记：
  - `primaryVideoUrl`
  - `fallbackVideoUrl`

### 6.4 封面图

优先路径：

```text
props.pageProps.metaOGInfo.data[0].content.cover.url
```

备选路径：

```text
props.pageProps.metaOGInfo.data[0].content.media.list[].url
where mediaType == "img"
```

忽略路径：

```text
mediaType == "blur"
```

建议：

- `cover.url` 作为主封面
- `media.list[img]` 作为补充图片池
- 对 URL 做去重
- `blur` 图不入库，不下载

### 6.5 作者信息

路径：

```text
props.pageProps.metaOGInfo.data[0].userInfo
```

当前样本：

- `userName`: `关你西红柿什么`
- `icon`: 作者头像 URL

可选用途：

- 存到 `Product.description`
- 存到素材元数据 / 审计字段

---

## 7. 推荐的 Python 解析骨架

```python
from typing import Any


def parse_dewu_next_data(next_data: dict[str, Any]) -> dict[str, Any]:
    page_props = next_data.get("props", {}).get("pageProps", {})
    meta = page_props.get("metaOGInfo", {})
    items = meta.get("data") or []
    first = items[0] if items else {}

    content = first.get("content") or {}
    user = first.get("userInfo") or {}
    media_list = (content.get("media") or {}).get("list") or []

    video_urls = [item.get("url") for item in media_list if item.get("mediaType") == "video" and item.get("url")]
    image_urls = [item.get("url") for item in media_list if item.get("mediaType") == "img" and item.get("url")]

    raw_content = (content.get("content") or "").strip()
    topics = [part.strip() for part in raw_content.split("#") if part.strip()]

    cover_url = (content.get("cover") or {}).get("url")
    if cover_url and cover_url not in image_urls:
        image_urls.insert(0, cover_url)

    return {
        "trendId": page_props.get("trendId"),
        "shareId": page_props.get("shareId"),
        "pageLink": page_props.get("pageLink"),
        "title": content.get("title"),
        "rawContent": raw_content,
        "topics": topics,
        "primaryCoverUrl": cover_url,
        "imageUrls": image_urls,
        "primaryVideoUrl": video_urls[0] if video_urls else None,
        "fallbackVideoUrl": content.get("videoShareUrl"),
        "authorName": user.get("userName"),
        "authorAvatarUrl": user.get("icon"),
    }
```

---

## 8. 风险与兼容性提示

1. `metaOGInfo.data` 是数组，当前样本只看到第一个元素有效，解析时不要写死只能存在一个。
2. `contentType=1` 在当前样本里可推断为视频动态，但不要把这个值的语义写死到所有页面。
3. `videoShareUrl` 看起来是带水印 / 算法处理版本，不应默认优先。
4. `image-cdn.dewu.com` 与 `image-cdn.poizon.com` 可能同时出现，属于 CDN 域名差异，不应简单按域名去重，应该按完整 URL 或下载后 hash 去重。
5. `query`、`routeQuery`、`pageLink` 中的 `trendId/shareId/source` 可作为页面定位信息，建议一起保留。
6. 页面如果后续改版，最容易变化的是：
   - `metaOGInfo` 包裹层
   - `data[0]` 的结构
   - `media.list` 的 `mediaType` 枚举值

---

## 9. 本样本的结论

基于当前这段 `__NEXT_DATA__`，可以稳定抽出以下核心素材：

- 标题：`空军一号 新款爱了爱了`
- 话题：5 个
- 无水印视频：1 个
- 主封面：1 个
- 备选图片：1 个
- 模糊图：1 个（应忽略）
- 作者名：`关你西红柿什么`
- 页面标识：`trendId=303342107`, `shareId=7EYGAmy`

因此，对当前项目来说，`__NEXT_DATA__` 已经足够作为**得物分享页素材解析的主数据源**。
