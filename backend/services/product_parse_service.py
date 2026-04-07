"""
得物掘金工具 - 商品素材解析服务
"""
import re
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from core.config import settings
from models import Product, Video, Cover, Copywriting, Topic, ProductTopic


# ============ 数据结构 ============

@dataclass
class MaterialPack:
    """从得物商品页解析出的素材包"""
    cover_urls: list[str]
    video_url: Optional[str]
    title: str
    topics: list[str]


# ============ HTTP 请求头 ============

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

_REQUEST_TIMEOUT = 30.0


# ============ 页面解析 ============

async def parse_product_page(dewu_url: str) -> MaterialPack:
    """
    用 httpx 请求得物商品页 HTML，解析素材信息。

    注意：非登录方式，直接 GET 请求，不使用 Patchright 浏览器。

    TODO: 得物商品页 DOM 结构未知，以下选择器为占位实现，
          需根据实际页面 HTML 调整正则表达式。
    """
    logger.info("开始解析得物商品页: url={}", dewu_url)

    async with httpx.AsyncClient(headers=_HEADERS, timeout=_REQUEST_TIMEOUT, follow_redirects=True) as client:
        try:
            response = await client.get(dewu_url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.warning("商品页请求失败: url={}, status={}", dewu_url, e.response.status_code)
            raise ValueError(f"商品页请求失败: HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("商品页网络错误: url={}, error_type={}", dewu_url, type(e).__name__)
            raise ValueError("商品页网络请求失败")

    html = response.text
    return _extract_material_pack(html, dewu_url)


def _extract_material_pack(html: str, dewu_url: str) -> MaterialPack:
    """
    从 HTML 中提取素材信息。

    TODO: 以下正则为占位实现，返回 mock 数据。
          需根据实际得物商品页 HTML 结构调整：
          - 封面图：查找 og:image 或商品主图 <img> 标签
          - 视频：查找 <video src="..."> 或 JSON-LD 中的 video 字段
          - 标题：查找 og:title 或 <h1> 商品名
          - 话题：查找商品标签/分类区域
    """
    # --- 标题：优先 og:title，其次 <title> ---
    title = _extract_og_title(html) or _extract_page_title(html) or "未知商品"

    # --- 封面图：og:image ---
    cover_urls = _extract_og_images(html)

    # --- 视频：<video> 标签或 JSON 字段 ---
    video_url = _extract_video_url(html)

    # --- 话题：商品标签 ---
    topics = _extract_topics(html)

    # TODO: 如果以上均未解析到有效数据，说明页面结构与预期不符，
    #       需要打印 html[:2000] 到日志（debug 级别）辅助调试。
    if not cover_urls and not video_url:
        logger.debug("商品页未解析到媒体资源，可能需要调整选择器: url={}", dewu_url)
        # mock 数据，保证流程可跑通
        cover_urls = []
        video_url = None

    logger.info(
        "商品页解析完成: title={}, covers={}, has_video={}, topics={}",
        title, len(cover_urls), video_url is not None, topics,
    )
    return MaterialPack(
        cover_urls=cover_urls,
        video_url=video_url,
        title=title,
        topics=topics,
    )


def _extract_og_title(html: str) -> Optional[str]:
    # TODO: 根据实际页面调整
    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']', html)
    return m.group(1).strip() if m else None


def _extract_page_title(html: str) -> Optional[str]:
    m = re.search(r'<title[^>]*>([^<]+)</title>', html)
    return m.group(1).strip() if m else None


def _extract_og_images(html: str) -> list[str]:
    # TODO: 根据实际页面调整，得物商品图可能在 JSON-LD 或自定义属性中
    urls: list[str] = []
    for m in re.finditer(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html):
        urls.append(m.group(1))
    for m in re.finditer(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html):
        url = m.group(1)
        if url not in urls:
            urls.append(url)
    return urls


def _extract_video_url(html: str) -> Optional[str]:
    # TODO: 根据实际页面调整
    m = re.search(r'<video[^>]+src=["\']([^"\']+)["\']', html)
    if m:
        return m.group(1)
    # JSON 字段 "videoUrl":"..."
    m = re.search(r'"videoUrl"\s*:\s*"([^"]+)"', html)
    return m.group(1) if m else None


def _extract_topics(html: str) -> list[str]:
    # TODO: 根据实际页面调整，得物话题可能在标签/分类区域
    topics: list[str] = []
    for m in re.finditer(r'"tag(?:Name)?"\s*:\s*"([^"]+)"', html):
        name = m.group(1).strip()
        if name and name not in topics:
            topics.append(name)
    return topics[:10]  # 最多取 10 个


# ============ 文件下载 ============

async def download_file(url: str, save_dir: str, filename: str) -> str:
    """
    用 httpx 下载媒体文件到本地，返回保存的绝对路径。
    """
    save_path = Path(save_dir) / filename
    save_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("开始下载文件: filename={}", filename)

    async with httpx.AsyncClient(headers=_HEADERS, timeout=60.0, follow_redirects=True) as client:
        try:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with open(save_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
        except httpx.HTTPStatusError as e:
            logger.warning("文件下载失败: filename={}, status={}", filename, e.response.status_code)
            raise ValueError(f"文件下载失败: HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error("文件下载网络错误: filename={}, error_type={}", filename, type(e).__name__)
            raise ValueError("文件下载网络请求失败")

    file_size = save_path.stat().st_size
    logger.info("文件下载完成: filename={}, size={}", filename, file_size)
    return str(save_path.resolve())


# ============ 完整流程编排 ============

async def parse_and_create_materials(
    db: AsyncSession,
    product: Product,
) -> dict:
    """
    完整素材解析流程：
    1. 解析商品页获取 MaterialPack
    2. 下载封面图和视频到本地
    3. 覆盖更新数据库素材记录（删旧建新）
    4. 部分失败不阻塞整体

    返回 ParseMaterialsResponse 兼容的 dict。
    """
    if not product.dewu_url:
        raise ValueError("商品未配置得物商品页 URL")

    product_id = product.id
    timestamp = int(datetime.utcnow().timestamp())

    # Step 1: 解析页面
    try:
        pack = await parse_product_page(product.dewu_url)
    except ValueError:
        raise

    # Step 2: 准备存储目录
    video_dir = "data/materials/videos"
    cover_dir = "data/materials/covers"
    Path(video_dir).mkdir(parents=True, exist_ok=True)
    Path(cover_dir).mkdir(parents=True, exist_ok=True)

    downloaded_videos: list[str] = []
    downloaded_covers: list[str] = []
    errors: list[str] = []

    # Step 3: 下载视频（部分失败不阻塞）
    if pack.video_url:
        video_filename = f"{product_id}_{timestamp}.mp4"
        try:
            path = await download_file(pack.video_url, video_dir, video_filename)
            downloaded_videos.append(path)
        except ValueError as e:
            logger.warning("视频下载失败，跳过: product_id={}, error={}", product_id, str(e))
            errors.append(f"视频下载失败: {e}")

    # Step 4: 下载封面图（部分失败不阻塞）
    for idx, cover_url in enumerate(pack.cover_urls):
        cover_filename = f"{product_id}_{timestamp}_{idx}.jpg"
        try:
            path = await download_file(cover_url, cover_dir, cover_filename)
            downloaded_covers.append(path)
        except ValueError as e:
            logger.warning("封面下载失败，跳过: product_id={}, idx={}, error={}", product_id, idx, str(e))
            errors.append(f"封面[{idx}]下载失败: {e}")

    # Step 5: 覆盖更新数据库 — 删除旧素材记录，创建新的
    await _replace_product_materials(
        db=db,
        product=product,
        pack=pack,
        video_paths=downloaded_videos,
        cover_paths=downloaded_covers,
    )

    logger.info(
        "商品素材解析完成: product_id={}, videos={}, covers={}, errors={}",
        product_id, len(downloaded_videos), len(downloaded_covers), len(errors),
    )

    return {
        "success": True,
        "product_id": product_id,
        "title": pack.title,
        "topics": pack.topics,
        "videos_downloaded": len(downloaded_videos),
        "covers_downloaded": len(downloaded_covers),
        "errors": errors,
    }


async def _replace_product_materials(
    db: AsyncSession,
    product: Product,
    pack: MaterialPack,
    video_paths: list[str],
    cover_paths: list[str],
) -> None:
    """删除商品旧素材记录，写入新记录。"""
    product_id = product.id

    # 删除旧视频（及其关联封面）
    old_videos_result = await db.execute(
        select(Video).where(Video.product_id == product_id)
    )
    old_videos = old_videos_result.scalars().all()
    for v in old_videos:
        await db.execute(delete(Cover).where(Cover.video_id == v.id))
    await db.execute(delete(Video).where(Video.product_id == product_id))

    # 删除旧文案（来源 parsed）
    await db.execute(
        delete(Copywriting).where(
            Copywriting.product_id == product_id,
            Copywriting.source_type == "parsed",
        )
    )

    # 删除旧话题关联
    await db.execute(
        delete(ProductTopic).where(ProductTopic.product_id == product_id)
    )

    # 写入新视频记录
    new_video_orm: list[Video] = []
    for path in video_paths:
        file_size = Path(path).stat().st_size if Path(path).exists() else None
        v = Video(
            product_id=product_id,
            name=f"{product.name}_视频",
            file_path=path,
            file_size=file_size,
            source_type="parsed",
        )
        db.add(v)
        new_video_orm.append(v)

    await db.flush()  # 获取 video.id

    # 写入新封面记录（关联第一个视频，若有）
    first_video_id = new_video_orm[0].id if new_video_orm else None
    for path in cover_paths:
        file_size = Path(path).stat().st_size if Path(path).exists() else None
        c = Cover(
            video_id=first_video_id,
            file_path=path,
            file_size=file_size,
        )
        db.add(c)

    # 写入文案（标题作为文案）
    if pack.title and pack.title != "未知商品":
        cw = Copywriting(
            product_id=product_id,
            content=pack.title,
            source_type="parsed",
            source_ref=product.dewu_url,
        )
        db.add(cw)

    # 写入话题关联（upsert topic by name）
    for topic_name in pack.topics:
        topic_result = await db.execute(
            select(Topic).where(Topic.name == topic_name)
        )
        topic = topic_result.scalars().first()
        if not topic:
            topic = Topic(name=topic_name, source="parsed")
            db.add(topic)
            await db.flush()

        pt = ProductTopic(product_id=product_id, topic_id=topic.id)
        db.add(pt)

    await db.commit()
    logger.info("商品素材数据库记录更新完成: product_id={}", product_id)

        super().__init__(detail)
