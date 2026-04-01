"""
得物掘金工具 - 得物平台客户端
"""
import asyncio
from typing import Optional, Tuple
from playwright.async_api import Page
from loguru import logger

from core.browser import browser_manager


class DewuClient:
    """得物平台 API 客户端（基于 Playwright 自动化）"""

    BASE_URL = "https://creator.dewu.com"
    LOGIN_URL = "https://creator.dewu.com/passport/login"
    UPLOAD_URL = "https://creator.dewu.com/content/video/upload"
    PUBLISH_URL = "https://creator.dewu.com/content/publish"

    def __init__(self, account_id: int):
        self.account_id = account_id
        self.page: Optional[Page] = None
        self.logged_in = False

    async def login(self) -> Tuple[bool, str]:
        """
        登录得物创作平台
        返回: (成功标志, 消息)
        """
        try:
            # 创建新页面
            self.page = await browser_manager.new_page(self.account_id)
            if not self.page:
                return False, "创建浏览器页面失败"

            logger.info(f"账号 {self.account_id} 开始登录得物")

            # 访问登录页面
            await self.page.goto(self.LOGIN_URL, wait_until="networkidle", timeout=60000)

            # 等待用户扫码或输入登录
            # 这里需要人工介入，可以通过截图让用户确认
            await self.page.wait_for_timeout(1000)

            # 检查是否登录成功（可以通过检查特定元素）
            try:
                await self.page.wait_for_selector(
                    '[class*="user-info"]',
                    timeout=300000  # 5分钟等待用户扫码
                )
                self.logged_in = True
                logger.info(f"账号 {self.account_id} 登录成功")
                return True, "登录成功"

            except Exception:
                # 可能是二维码过期或其他问题
                return False, "登录超时或失败"

        except Exception as e:
            logger.error(f"账号 {self.account_id} 登录失败: {e}")
            return False, str(e)

    async def check_login_status(self) -> Tuple[bool, str]:
        """检查登录状态"""
        try:
            if not self.page:
                self.page = await browser_manager.new_page(self.account_id)

            # 访问主页检查登录状态
            await self.page.goto(self.BASE_URL, wait_until="networkidle", timeout=30000)

            # 检查是否跳转到登录页
            if "login" in self.page.url:
                self.logged_in = False
                return False, "未登录"

            self.logged_in = True
            return True, "已登录"

        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False, str(e)

    async def get_user_info(self) -> Optional[dict]:
        """获取用户信息"""
        if not self.logged_in:
            return None

        try:
            # 访问用户信息页面
            await self.page.goto(f"{self.BASE_URL}/user/profile", wait_until="networkidle")

            # 提取用户信息（需要根据实际页面结构调整）
            info = await self.page.evaluate("""
                () => {
                    const nameEl = document.querySelector('[class*="user-name"]');
                    const avatarEl = document.querySelector('[class*="avatar"] img');
                    return {
                        name: nameEl?.textContent?.trim() || '未知',
                        avatar: avatarEl?.src || ''
                    };
                }
            """)

            return info

        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None

    async def upload_video(self, video_path: str, title: str, content: str,
                          topic: str = "", cover_path: str = None) -> Tuple[bool, str]:
        """
        上传视频
        返回: (成功标志, 消息/视频ID)
        """
        if not self.logged_in:
            return False, "未登录"

        try:
            # 访问发布页面
            await self.page.goto(self.UPLOAD_URL, wait_until="networkidle")

            # 上传视频文件
            file_input = await self.page.wait_for_selector('input[type="file"]', timeout=10000)
            await file_input.set_input_files(video_path)

            logger.info(f"账号 {self.account_id} 视频上传中: {video_path}")

            # 等待上传完成（进度条消失）
            await self.page.wait_for_selector(
                '[class*="upload-progress"]',
                state="hidden",
                timeout=300000  # 5分钟上传超时
            )

            # 填写标题
            title_input = await self.page.wait_for_selector(
                'textarea[class*="title"], input[class*="title"]',
                timeout=10000
            )
            await title_input.fill(title)

            # 填写内容
            content_input = await self.page.wait_for_selector(
                'div[class*="content"] [contenteditable="true"]',
                timeout=10000
            )
            await content_input.fill(content)

            # 添加话题
            if topic:
                topic_input = await self.page.wait_for_selector(
                    'input[class*="topic"]',
                    timeout=5000
                )
                await topic_input.fill(topic)

            # 上传封面
            if cover_path:
                cover_input = await self.page.wait_for_selector(
                    'input[class*="cover"]',
                    timeout=5000
                )
                await cover_input.set_input_files(cover_path)

            # 点击发布按钮
            publish_btn = await self.page.wait_for_selector(
                'button[class*="publish"], button:has-text("发布")',
                timeout=10000
            )
            await publish_btn.click()

            # 等待发布成功
            await self.page.wait_for_selector(
                '[class*="success"], .toast:has-text("发布成功")',
                timeout=30000
            )

            logger.info(f"账号 {self.account_id} 视频发布成功")
            return True, "发布成功"

        except Exception as e:
            logger.error(f"账号 {self.account_id} 视频发布失败: {e}")
            return False, str(e)

    async def get_dashboard_stats(self) -> Optional[dict]:
        """获取仪表盘统计数据"""
        if not self.logged_in:
            return None

        try:
            await self.page.goto(f"{self.BASE_URL}/dashboard", wait_until="networkidle")

            stats = await self.page.evaluate("""
                () => {
                    const items = document.querySelectorAll('[class*="stat-item"]');
                    const data = {};
                    items.forEach(item => {
                        const label = item.querySelector('[class*="label"]')?.textContent;
                        const value = item.querySelector('[class*="value"]')?.textContent;
                        if (label && value) {
                            data[label] = value;
                        }
                    });
                    return data;
                }
            """)

            return stats

        except Exception as e:
            logger.error(f"获取统计数据失败: {e}")
            return None

    async def screenshot_login(self, path: str = "logs/login.png"):
        """截取登录页面"""
        if self.page:
            await self.page.screenshot(path=path, full_page=True)
            logger.info(f"登录页面截图已保存: {path}")

    async def close(self):
        """关闭客户端"""
        if self.page:
            await self.page.close()
            self.page = None
            self.logged_in = False


async def get_dewu_client(account_id: int) -> DewuClient:
    """获取得物客户端"""
    return DewuClient(account_id)
