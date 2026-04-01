"""
得物掘金工具 - Playwright 浏览器管理
"""
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from loguru import logger

from core.config import settings
from utils.crypto import encrypt_data, decrypt_data


class BrowserManager:
    """Playwright 浏览器管理器"""

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.contexts: Dict[int, BrowserContext] = {}  # account_id -> context
        self._lock = asyncio.Lock()

    async def init(self):
        """初始化 Playwright"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            logger.info(f"Playwright 浏览器已启动 (headless={settings.PLAYWRIGHT_HEADLESS})")

    async def close(self):
        """关闭浏览器"""
        async with self._lock:
            for context in self.contexts.values():
                await context.close()
            self.contexts.clear()

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            logger.info("Playwright 浏览器已关闭")

    async def create_context(self, account_id: int, storage_state: Optional[str] = None) -> BrowserContext:
        """为账号创建浏览器上下文"""
        await self.init()

        async with self._lock:
            # 如果已存在，先关闭
            if account_id in self.contexts:
                await self.contexts[account_id].close()

            # 创建新上下文
            context = await self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            # 如果有存储状态，加载它
            if storage_state:
                try:
                    state_data = decrypt_data(storage_state)
                    state = json.loads(state_data)
                    await context.set_storage_state(state)
                    logger.info(f"账号 {account_id} 加载存储状态成功")
                except Exception as e:
                    logger.warning(f"加载存储状态失败: {e}")

            self.contexts[account_id] = context
            return context

    async def get_context(self, account_id: int) -> Optional[BrowserContext]:
        """获取账号的浏览器上下文"""
        return self.contexts.get(account_id)

    async def get_or_create_context(self, account_id: int, storage_state: Optional[str] = None) -> BrowserContext:
        """获取或创建浏览器上下文"""
        context = await self.get_context(account_id)
        if not context:
            context = await self.create_context(account_id, storage_state)
        return context

    async def save_storage_state(self, account_id: int) -> Optional[str]:
        """保存账号的存储状态"""
        context = await self.get_context(account_id)
        if not context:
            return None

        try:
            state = await context.storage_state()
            state_json = json.dumps(state)
            encrypted = encrypt_data(state_json)
            logger.info(f"账号 {account_id} 存储状态已保存")
            return encrypted
        except Exception as e:
            logger.error(f"保存存储状态失败: {e}")
            return None

    async def new_page(self, account_id: int) -> Optional[Page]:
        """为账号创建新页面"""
        context = await self.get_or_create_context(account_id)
        if context:
            page = await context.new_page()
            return page
        return None

    async def close_context(self, account_id: int):
        """关闭账号的浏览器上下文"""
        async with self._lock:
            if account_id in self.contexts:
                await self.contexts[account_id].close()
                del self.contexts[account_id]
                logger.info(f"账号 {account_id} 上下文已关闭")

    async def screenshot(self, account_id: int, path: str):
        """截图"""
        context = await self.get_context(account_id)
        if context:
            pages = context.pages
            if pages:
                await pages[0].screenshot(path=path)


# 全局浏览器管理器实例
browser_manager = BrowserManager()


async def get_browser_manager() -> BrowserManager:
    """获取浏览器管理器"""
    return browser_manager
