"""
得物掘金工具 - Patchright 浏览器管理（反检测版本）
"""
import asyncio
import json
from typing import Optional, Dict
from patchright.async_api import async_playwright
from loguru import logger

from core.config import settings
from utils.crypto import encrypt_data, decrypt_data


class BrowserManager:
    """Patchright 浏览器管理器（反检测）"""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.contexts: Dict[int, any] = {}  # account_id -> context
        self._lock = asyncio.Lock()

    async def init(self):
        """初始化 Patchright 浏览器"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
            )
            logger.info(f"Patchright 浏览器已启动 (headless={settings.PLAYWRIGHT_HEADLESS})")

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

            logger.info("Patchright 浏览器已关闭")

    async def create_context(self, account_id: int, storage_state: Optional[str] = None):
        """为账号创建浏览器上下文"""
        await self.init()

        async with self._lock:
            # 如果已存在，先关闭
            if account_id in self.contexts:
                await self.contexts[account_id].close()

            # 创建新上下文
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
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

    async def get_context(self, account_id: int):
        """获取账号的浏览器上下文"""
        return self.contexts.get(account_id)

    async def get_or_create_context(self, account_id: int, storage_state: Optional[str] = None):
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

    async def new_page(self, account_id: int):
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


class PreviewBrowserManager:
    """独立的 headed 浏览器管理器，用于账号预览"""

    def __init__(self) -> None:
        self.playwright = None
        self.browser = None
        self._current_account_id: Optional[int] = None
        self._context = None
        self._page = None
        self._lock = asyncio.Lock()

    async def open(self, account_id: int, storage_state: Optional[str] = None) -> bool:
        """打开预览浏览器"""
        async with self._lock:
            # 如果已有预览窗口打开，先关闭
            if self._current_account_id is not None:
                await self._close_internal()

            # 启动 headed 浏览器
            if not self.playwright:
                self.playwright = await async_playwright().start()
            if not self.browser:
                self.browser = await self.playwright.chromium.launch(headless=False)

            # 创建 context
            self._context = await self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )

            # 加载 storage_state
            if storage_state:
                try:
                    state_data = decrypt_data(storage_state)
                    state = json.loads(state_data)
                    await self._context.set_storage_state(state)
                    logger.info("账号 {} 预览 storage_state 加载成功", account_id)
                except Exception as e:
                    logger.warning("预览浏览器加载 storage_state 失败: {}", e)

            # 打开页面
            self._page = await self._context.new_page()
            await self._page.goto("https://creator.dewu.com", timeout=30000)

            self._current_account_id = account_id

            # 监听浏览器断开（用户手动关闭窗口）
            self.browser.on("disconnected", lambda _: self._on_browser_closed())

            logger.info("账号 {} 预览浏览器已打开", account_id)
            return True

    async def close(self, save_session: bool = False) -> Optional[str]:
        """关闭预览浏览器，可选保存 session"""
        async with self._lock:
            return await self._close_internal(save_session)

    async def _close_internal(self, save_session: bool = False) -> Optional[str]:
        """内部关闭方法（调用前必须持有锁）"""
        saved_state = None
        if save_session and self._context:
            try:
                state = await self._context.storage_state()
                state_json = json.dumps(state)
                saved_state = encrypt_data(state_json)
                logger.info("预览 session 已保存: account_id={}", self._current_account_id)
            except Exception as e:
                logger.warning("保存预览 session 失败: {}", e)

        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None
            self._page = None

        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None

        self._current_account_id = None
        return saved_state

    def _on_browser_closed(self) -> None:
        """浏览器被用户手动关闭时的回调"""
        self._current_account_id = None
        self._context = None
        self._page = None
        self.browser = None
        self.playwright = None
        logger.info("预览浏览器已被用户关闭")

    @property
    def is_open(self) -> bool:
        return self._current_account_id is not None

    @property
    def current_account_id(self) -> Optional[int]:
        return self._current_account_id


# 全局预览浏览器管理器实例
preview_manager = PreviewBrowserManager()
