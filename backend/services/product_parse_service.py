"""
得物掘金工具 - 商品素材解析服务
"""
import json
import re
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from core.browser import browser_manager
from core.config import settings
from models import Product, Video, Cover, Copywriting, Topic, ProductTopic
from services.media_storage_service import MediaStorageService


# ============ 数据结构 ============

@dataclass
class MaterialPack:
    """从得物商品页解析出的素材包"""
    cover_urls: list[str]
    video_url: Optional[str]
    title: str
    topics: list[str]


# ============ 页面解析 ============

async def parse_product_page(dewu_url: str) -> MaterialPack:
    """
    用 Patchright 浏览器渲染得物商品页 HTML，解析素材信息。

    得物为 CSR（客户端渲染），必须通过浏览器执行 JS 后才能获取完整 DOM。
    使用匿名 context（公开页面无需登录）。
    """
    logger.info("开始解析得物商品页: url={}", dewu_url)

    await browser_manager.init()

    context = await browser_manager.browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
    )
    page = await context.new_page()

    try:
        await page.goto(dewu_url, timeout=15000)
        try:
            await page.wait_for_selector('div[class*="pc_title__"]', timeout=15000)
        except Exception:
            # 选择器未出现时降级等待 networkidle
            await page.wait_for_load_state("networkidle", timeout=15000)

        html = await page.content()
        logger.info("商品页渲染完成: url={}, html_len={}", dewu_url, len(html))

        # 保存渲染后的 HTML 用于调试（仅 DEBUG 模式）
        if settings.DEBUG:
            debug_dir = Path("data/debug")
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = debug_dir / f"parse_{int(datetime.now(datetime.UTC).timestamp())}.html"
            debug_path.write_text(html, encoding="utf-8")
            logger.info("渲染 HTML 已保存: path={}", debug_path)
    except Exception as e:
        logger.error("商品页浏览器渲染失败: url={}, error_type={}", dewu_url, type(e).__name__)
        raise ValueError(f"商品页渲染失败: {type(e).__name__}")
    finally:
        await page.close()
        await context.close()

    return _extract_material_pack(html, dewu_url)


def _extract_material_pack(html: str, dewu_url: str) -> MaterialPack:
    """从得物社区动态页 HTML 中提取素材信息。"""
    title = _extract_title(html) or "未知商品"
    cover_urls = _extract_cover_urls(html)
    video_url = _extract_video_url(html)
    topics = _extract_topics(html)

    if not cover_urls and not video_url:
        logger.debug("商品页未解析到媒体资源: url={}", dewu_url)

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


def _extract_next_data(html: str) -> Optional[dict]:
    """从 <script id="__NEXT_DATA__"> 提取并解析 JSON。"""
    m = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except (ValueError, TypeError):
        logger.debug("__NEXT_DATA__ JSON 解析失败")
        return None


def _extract_title(html: str) -> Optional[str]:
    """提取标题: 优先从 __NEXT_DATA__ content.title，fallback 到 DOM 正则"""
    next_data = _extract_next_data(html)
    if next_data is not None:
        try:
            title = next_data["props"]["pageProps"]["metaOGInfo"]["data"][0]["content"]["title"]
            if title:
                return str(title).strip()
        except (KeyError, TypeError, IndexError):
            pass

    # fallback: DOM 正则
    m = re.search(r'<div\s+class="pc_title__[^"]*"[^>]*>([^<]+)</div>', html)
    if m:
        return m.group(1).strip()
    # fallback: og:title
    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']', html)
    return m.group(1).strip() if m else None


def _extract_cover_urls(html: str) -> list[str]:
    """提取封面图: 优先从 __NEXT_DATA__ content.cover.url + media.list[img]，fallback 到 DOM 正则"""
    next_data = _extract_next_data(html)
    if next_data is not None:
        try:
            content = next_data["props"]["pageProps"]["metaOGInfo"]["data"][0]["content"]
            seen: set[str] = set()
            urls: list[str] = []

            # 主封面优先
            cover_url = content.get("cover", {}).get("url")
            if cover_url:
                seen.add(cover_url)
                urls.append(cover_url)

            # 补充 media.list[mediaType=img]，跳过 blur，去重
            for item in content.get("media", {}).get("list", []):
                if item.get("mediaType") == "img" and item.get("url") and item["url"] not in seen:
                    seen.add(item["url"])
                    urls.append(item["url"])

            if urls:
                return urls
        except (KeyError, TypeError, IndexError):
            pass

    # fallback: DOM 正则
    urls = []
    m = re.search(r'<video[^>]+poster=["\']([^"\']+)["\']', html)
    if m:
        urls.append(m.group(1))
    for m in re.finditer(r'<img[^>]+class="Products_item-pic__[^"]*"[^>]+src=["\']([^"\']+)["\']', html):
        url = m.group(1)
        if url not in urls:
            urls.append(url)
    if not urls:
        for m in re.finditer(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html):
            urls.append(m.group(1))
    return urls


def _extract_video_url(html: str) -> Optional[str]:
    """提取视频: 优先从 __NEXT_DATA__ media.list[video]，备选 videoShareUrl，fallback 到 DOM 正则"""
    next_data = _extract_next_data(html)
    if next_data is not None:
        try:
            content = next_data["props"]["pageProps"]["metaOGInfo"]["data"][0]["content"]

            # 无水印版优先
            for item in content.get("media", {}).get("list", []):
                if item.get("mediaType") == "video" and item.get("url"):
                    return item["url"]

            # 带水印备选
            share_url = content.get("videoShareUrl")
            if share_url:
                return share_url
        except (KeyError, TypeError, IndexError):
            pass

    # fallback: DOM 正则
    m = re.search(r'<video[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\']', html)
    if m:
        return m.group(1)
    m = re.search(r'<source[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\']', html)
    return m.group(1) if m else None


def _extract_topics(html: str) -> list[str]:
    """提取话题: 优先从 __NEXT_DATA__ JSON content 字段解析 #tag，fallback 到 DOM 正则"""
    next_data = _extract_next_data(html)
    if next_data is not None:
        try:
            content_text = next_data["props"]["pageProps"]["metaOGInfo"]["data"][0]["content"]["content"]
            if content_text:
                topics = [
                    token.lstrip('#').strip()
                    for token in content_text.split()
                    if token.startswith('#') and len(token) > 1
                ]
                # deduplicate while preserving order
                seen: set[str] = set()
                unique = [t for t in topics if not (t in seen or seen.add(t))]  # type: ignore[func-returns-value]
                if unique:
                    return unique[:20]
        except (KeyError, TypeError, IndexError):
            pass

    # fallback: DOM 正则
    topics: list[str] = []
    content_m = re.search(r'<div\s+class="pc_content__[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    if content_m:
        content_html = content_m.group(1)
        for m in re.finditer(r'<span[^>]+data-id="[^"]*"[^>]*>\s*#?([^<]+)</span>', content_html):
            name = m.group(1).strip().lstrip('#').strip()
            if name and name not in topics:
                topics.append(name)
    if not topics:
        for m in re.finditer(r'onclick="window\.DEWU\.onClickTag[^"]*"[^>]*>\s*#([^<]+)</span>', html):
            name = m.group(1).strip()
            if name and name not in topics:
                topics.append(name)
    return topics[:20]


# ============ 完整流程编排 ============

async def parse_and_create_materials(
    db: AsyncSession,
    product: Product,
) -> dict:
    """
    完整素材解析流程：
    1. 解析商品页获取 MaterialPack
    2. 通过 MediaStorageService 下载封面图和视频到内容寻址存储
    3. 覆盖更新数据库素材记录（删旧建新）
    4. 更新 product 的反范式计数字段和 parse_status
    5. 部分失败不阻塞整体

    返回 ParseMaterialsResponse 兼容的 dict。
    """
    if not product.dewu_url:
        raise ValueError("商品未配置得物商品页 URL")

    product_id = product.id
    media_storage = MediaStorageService()

    # Step 1: 解析页面
    try:
        pack = await parse_product_page(product.dewu_url)
    except ValueError:
        raise

    downloaded_videos: list[tuple[str, str, int]] = []
    downloaded_covers: list[tuple[str, str, int]] = []
    errors: list[str] = []

    # Step 2: 下载视频（部分失败不阻塞）
    if pack.video_url:
        try:
            result = await media_storage.store_from_url(pack.video_url, "videos")
            downloaded_videos.append(result)
        except Exception as e:
            logger.warning("视频下载失败，跳过: product_id={}, error_type={}", product_id, type(e).__name__)
            errors.append(f"视频下载失败: {type(e).__name__}")

    # Step 3: 下载封面图（部分失败不阻塞）
    for idx, cover_url in enumerate(pack.cover_urls):
        try:
            result = await media_storage.store_from_url(cover_url, "covers")
            downloaded_covers.append(result)
        except Exception as e:
            logger.warning("封面下载失败，跳过: product_id={}, idx={}, error_type={}", product_id, idx, type(e).__name__)
            errors.append(f"封面[{idx}]下载失败: {type(e).__name__}")

    # Step 4: 覆盖更新数据库 — 删除旧素材记录，创建新的
    counts = await _replace_product_materials(
        db=db,
        product=product,
        pack=pack,
        video_results=downloaded_videos,
        cover_results=downloaded_covers,
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
        **counts,
    }



async def _delete_old_materials(db: AsyncSession, product_id: int) -> None:
    """删除商品的全部旧素材记录（视频、封面、文案、话题关联）。"""
    old_videos_result = await db.execute(
        select(Video).where(Video.product_id == product_id)
    )
    for v in old_videos_result.scalars().all():
        await db.execute(delete(Cover).where(Cover.video_id == v.id))
    await db.execute(delete(Video).where(Video.product_id == product_id))
    await db.execute(delete(Cover).where(Cover.product_id == product_id))
    await db.execute(
        delete(Copywriting).where(
            Copywriting.product_id == product_id,
            Copywriting.source_type == "dewu_parse",
        )
    )
    await db.execute(delete(ProductTopic).where(ProductTopic.product_id == product_id))


async def _insert_new_videos(
    db: AsyncSession,
    product_id: int,
    pack: MaterialPack,
    product_name: str,
    video_results: list[tuple[str, str, int]],
) -> list[Video]:
    """写入新视频记录，flush 以获取 id，返回 ORM 列表。"""
    new_video_orm: list[Video] = []
    for file_path, file_hash, file_size in video_results:
        v = Video(
            product_id=product_id,
            name=f"{pack.title}_视频" if pack.title != "未知商品" else f"{product_name}_视频",
            file_path=file_path,
            file_hash=file_hash,
            file_size=file_size,
            source_type="dewu_parse",
        )
        db.add(v)
        new_video_orm.append(v)
    await db.flush()
    return new_video_orm


def _insert_new_covers(
    db: AsyncSession,
    product_id: int,
    first_video_id: Optional[int],
    pack: MaterialPack,
    cover_results: list[tuple[str, str, int]],
) -> None:
    """写入新封面记录。"""
    for file_path, file_hash, file_size in cover_results:
        c = Cover(
            video_id=first_video_id,
            product_id=product_id,
            name=pack.title,
            file_path=file_path,
            file_hash=file_hash,
            file_size=file_size,
        )
        db.add(c)


def _insert_copywriting(
    db: AsyncSession,
    product: Product,
    pack: MaterialPack,
) -> int:
    """写入标题文案，更新 product.name，返回写入数量（0 或 1）。"""
    if not pack.title or pack.title == "未知商品":
        return 0
    cw = Copywriting(
        product_id=product.id,
        name=pack.title[:50],
        content=pack.title,
        source_type="dewu_parse",
        source_ref=product.dewu_url,
    )
    db.add(cw)
    product.name = pack.title
    return 1


async def _insert_topics(
    db: AsyncSession,
    product_id: int,
    topic_names: list[str],
) -> int:
    """Upsert 话题并写入 product_topics 关联，返回关联数量。"""
    count = 0
    for topic_name in topic_names:
        topic_result = await db.execute(select(Topic).where(Topic.name == topic_name))
        topic = topic_result.scalars().first()
        if not topic:
            topic = Topic(name=topic_name, source="dewu_parse")
            db.add(topic)
            await db.flush()
        db.add(ProductTopic(product_id=product_id, topic_id=topic.id))
        count += 1
    return count


async def _replace_product_materials(
    db: AsyncSession,
    product: Product,
    pack: MaterialPack,
    video_results: list[tuple[str, str, int]],
    cover_results: list[tuple[str, str, int]],
) -> dict[str, int]:
    """删除商品旧素材记录，写入新记录，更新反范式计数和 parse_status。

    返回包含各计数字段的 dict。
    """
    product_id = product.id

    await _delete_old_materials(db, product_id)

    new_video_orm = await _insert_new_videos(db, product_id, pack, product.name, video_results)

    first_video_id = new_video_orm[0].id if new_video_orm else None
    _insert_new_covers(db, product_id, first_video_id, pack, cover_results)

    copywriting_count = _insert_copywriting(db, product, pack)

    topic_count = await _insert_topics(db, product_id, pack.topics)

    video_count = len(new_video_orm)
    cover_count = len(cover_results)
    product.video_count = video_count
    product.cover_count = cover_count
    product.copywriting_count = copywriting_count
    product.topic_count = topic_count
    product.parse_status = "parsed"
    db.add(product)

    await db.commit()
    logger.info(
        "商品素材数据库记录更新完成: product_id={}, videos={}, covers={}, copywritings={}, topics={}",
        product_id, video_count, cover_count, copywriting_count, topic_count,
    )

    return {
        "video_count": video_count,
        "cover_count": cover_count,
        "copywriting_count": copywriting_count,
        "topic_count": topic_count,
    }
