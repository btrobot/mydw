# 得物页面数据结构说明

> 来源: `<script id="__NEXT_DATA__">` JSON
> 更新: 2026-04-08

## JSON 路径

```
props.pageProps.metaOGInfo.data[0].content
```

## 字段映射

```
content
├── title          → 标题/商品名 (string)
├── content        → 话题字符串 "#tag1 #tag2 ..." (空格分隔)
├── contentId      → 动态ID (int)
├── contentType    → 内容类型 (1=视频动态)
├── cover
│   ├── mediaType  → "img"
│   └── url        → 主封面图URL (高质量，优先使用)
├── media.list[]
│   ├── {mediaType:"video", url:"...mp4"}  → 视频(无水印，应下载此版本)
│   ├── {mediaType:"img",   url:"...jpg"}  → 封面图(可能与cover.url相同)
│   └── {mediaType:"blur",  url:"...jpg"}  → 模糊预览图(跳过，不下载)
├── videoShareUrl  → 视频(带水印版本，备选)
└── userInfo
    ├── userName   → 作者名
    └── icon       → 作者头像URL
```

## 素材提取规则

| 素材 | 取值路径 | 说明 |
|------|---------|------|
| 标题 | `content.title` | 用作 Product.name 和 Copywriting.content |
| 话题 | `content.content` | 按 `#` 分割，去掉前导 `#` 和空格 |
| 视频 | `media.list[mediaType=video].url` | 无水印版，优先下载 |
| 主封面 | `content.cover.url` | 独立字段，高质量 |
| 备选封面 | `media.list[mediaType=img].url` | 可能与 cover.url 相同，需去重 |
| 模糊图 | `media.list[mediaType=blur]` | 忽略，不下载 |
| 带水印视频 | `content.videoShareUrl` | 仅在无水印版不可用时备选 |
| 作者 | `userInfo.userName` | 可存入 Product.description |

## 页面元数据

```
props.pageProps
├── trendId      → 动态ID (string)
├── shareId      → 分享ID
├── source       → "videoTrend"
└── pageLink     → 完整页面链接
```

## 分享文本格式

```
{作者名}发布了一篇得物动态，https://dw4.co/t/A/{shareCode}点开链接，快来看吧！
```

URL 正则: `https?://(?:dw4\.co|(?:www\.)?dewu\.com)[A-Za-z0-9/\-_.?=&#%+~:]*`

注意: URL 和中文之间可能无空格，正则需在遇到非 ASCII 字符时停止匹配。
