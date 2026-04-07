"""
得物话题搜索服务
"""
import re
import asyncio
from typing import List, Dict

from patchright.async_api import async_playwright
from loguru import logger


def _parse_heat(text: str) -> int:
    """将热度文本解析为整数，如 '1.2万' -> 12000"""
    text = text.strip()
    try:
        if "亿" in text:
            return int(float(text.replace("亿", "")) * 100_000_000)
        if "万" in text:
            return int(float(text.replace("万", "")) * 10_000)
        digits = re.sub(r"[^\d]", "", text)
        return int(digits) if digits else 0
    except (ValueError, AttributeError):
        return 0


class TopicSearchService:
    """得物创作者平台话题搜索服务"""

    SEARCH_URL = "https://creator.dewu.com/topic/search"

    # 候选选择器（按优先级排列，取第一个命中的）
    _INPUT_SELECTORS = [
        'input[placeholder*="搜索话题"]',
        'input[placeholder*="话题"]',
        'input[type="search"]',
        'input[type="text"]',
    ]

    _ITEM_SELECTORS = [
        '[class*="topic-item"]',
        '[class*="topicItem"]',
        '[class*="topic_item"]',
        '[class*="list-item"]',
        '[class*="result-item"]',
    ]

    _NAME_SELECTORS = [
        '[class*="topic-name"]',
        '[class*="topicName"]',
        '[class*="name"]',
        '[class*="title"]',
        "span",
        "p",
    ]

    _HEAT_SELECTORS = [
        '[class*="heat"]',
        '[class*="hot"]',
        '[class*="count"]',
        '[class*="num"]',
        "em",
        "i",
    ]

    async def search(self, keyword: str) -> List[Dict]:
        """
        搜索得物话题

        Args:
            keyword: 搜索关键词

        Returns:
            List of {name: str, heat: int}
        """
        logger.info("开始搜索话题: keyword={}", keyword)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                    timezone_id="Asia/Shanghai",
                )
                page = await context.new_page()

                try:
                    await page.goto(self.SEARCH_URL, timeout=10_000)
                except Exception as e:
                    logger.warning("直接访问搜索页失败，尝试首页: {}", e)
                    await page.goto("https://creator.dewu.com", timeout=10_000)

                # 找到搜索输入框
                input_el = None
                for selector in self._INPUT_SELECTORS:
                    try:
                        input_el = await page.wait_for_selector(selector, timeout=3_000)
                        if input_el:
                            logger.debug("找到输入框: selector={}", selector)
                            break
                    except Exception:
                        continue

                if not input_el:
                    logger.warning("未找到话题搜索输入框，返回空结果")
                    return []

                # 输入关键词并触发搜索
                await input_el.fill(keyword)
                await input_el.press("Enter")

                # 等待结果加载
                results: List[Dict] = []
                item_el = None

                for selector in self._ITEM_SELECTORS:
                    try:
                        item_el = await page.wait_for_selector(selector, timeout=5_000)
                        if item_el:
                            logger.debug("找到结果列表: selector={}", selector)
                            break
                    except Exception:
                        continue

                if not item_el:
                    logger.warning("未找到话题结果列表，返回空结果")
                    return []

                # 提取所有结果项
                matched_selector = None
                for selector in self._ITEM_SELECTORS:
                    items = await page.query_selector_all(selector)
                    if items:
                        matched_selector = selector
                        break

                if not matched_selector:
                    return []

                items = await page.query_selector_all(matched_selector)
                logger.info("找到话题结果: count={}", len(items))

                for item in items:
                    name = ""
                    heat = 0

                    # 提取名称
                    for sel in self._NAME_SELECTORS:
                        try:
                            el = await item.query_selector(sel)
                            if el:
                                text = (await el.inner_text()).strip()
                                if text and "#" not in text[:1]:
                                    name = text.lstrip("#").strip()
                                elif text:
                                    name = text.lstrip("#").strip()
                                if name:
                                    break
                        except Exception:
                            continue

                    # 提取热度
                    for sel in self._HEAT_SELECTORS:
                        try:
                            el = await item.query_selector(sel)
                            if el:
                                text = (await el.inner_text()).strip()
                                if text:
                                    heat = _parse_heat(text)
                                    break
                        except Exception:
                            continue

                    if name:
                        results.append({"name": name, "heat": heat})

                logger.info("话题搜索完成: keyword={}, found={}", keyword, len(results))
                return results

            except asyncio.TimeoutError:
                logger.error("话题搜索超时: keyword={}", keyword)
                return []
            except Exception as e:
                logger.error("话题搜索失败: keyword={}, error={}", keyword, str(e))
                return []
            finally:
                await browser.close()
