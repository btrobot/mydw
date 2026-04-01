"""
得物掘金工具 - 得物平台客户端
"""
import asyncio
from typing import Optional, Tuple, Dict, Any
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from loguru import logger

from core.browser import browser_manager


# 登录页面元素选择器（已验证 Patchright）
LOGIN_SELECTORS = {
    "phone_input": [
        'input[placeholder*="手机"]',
        'input[type="text"]',
    ],
    "agree_checkbox": [
        'input[type="checkbox"]',
    ],
    "code_button": [
        'button:has-text("发送验证码")',
        'button:has-text("获取验证码")',
    ],
    "code_input": [
        'input[placeholder*="验证码"]',
    ],
    # 重要：优先使用 "登 录"（有空格），避免误点 "密码登录"
    "login_button": [
        'button:has-text("登 录")',
    ],
    # 登录成功后跳转的页面路径
    "logged_in_pages": [
        '/release',
        '/content',
        '/creator',
        '/dashboard',
    ],
    # 登录成功的页面标识
    "logged_in_indicator": [
        '[class*="user-info"]',
        '[class*="avatar"]',
        '[class*="nickname"]',
        '[class*="header-user"]',
        '.user-avatar',
        'header [class*="avatar"]',
    ],
    "error_message": [
        'ant-form-item-explain-error',
        '[class*="error"]',
        '[class*="wrong"]',
    ],
}


class DewuClient:
    """得物平台 API 客户端（基于 Playwright 自动化）"""

    BASE_URL = "https://creator.dewu.com"
    LOGIN_URL = "https://creator.dewu.com/login"
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

    async def login_with_sms(self, phone: str) -> Tuple[bool, str]:
        """
        通过手机验证码登录 - 第一步：发送验证码
        - 打开登录页面
        - 输入手机号
        - 点击获取验证码
        - 返回状态（由调用方处理验证码输入和提交）
        """
        try:
            # 创建新页面或使用现有页面
            if not self.page:
                self.page = await browser_manager.new_page(self.account_id)
                if not self.page:
                    return False, "创建浏览器页面失败"

            logger.info(f"账号 {self.account_id} 开始手机登录: phone={phone[:3]}***")

            # 访问登录页面
            await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(2000)  # 等待页面完全加载

            # 查找手机号输入框
            phone_input = None
            for selector in LOGIN_SELECTORS["phone_input"]:
                try:
                    phone_input = await self.page.wait_for_selector(selector, timeout=3000)
                    if phone_input:
                        logger.debug(f"找到手机号输入框: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not phone_input:
                # 保存截图用于调试
                await self.page.screenshot(path=f"logs/login_debug_{self.account_id}.png")
                return False, f"未找到手机号输入框，请检查页面元素"

            # 先勾选同意协议复选框
            for selector in LOGIN_SELECTORS["agree_checkbox"]:
                try:
                    checkbox = await self.page.wait_for_selector(selector, timeout=2000)
                    if checkbox:
                        # 检查是否已勾选
                        is_checked = await checkbox.is_checked()
                        if not is_checked:
                            await checkbox.check()
                            logger.debug(f"已勾选协议复选框: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            await self.page.wait_for_timeout(300)

            # 输入手机号
            await phone_input.fill(phone)
            await self.page.wait_for_timeout(500)

            # 查找验证码按钮
            code_button = None
            for selector in LOGIN_SELECTORS["code_button"]:
                try:
                    code_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if code_button:
                        logger.debug(f"找到验证码按钮: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not code_button:
                await self.page.screenshot(path=f"logs/login_debug_{self.account_id}.png")
                return False, "未找到验证码按钮，请检查页面元素"

            # 点击获取验证码
            await code_button.click()
            logger.info(f"账号 {self.account_id} 验证码已发送")
            await self.page.wait_for_timeout(1000)

            return True, "验证码已发送，请在5分钟内输入"

        except PlaywrightTimeout as e:
            logger.error(f"账号 {self.account_id} 等待元素超时: {e}")
            await self.page.screenshot(path=f"logs/login_timeout_{self.account_id}.png")
            return False, f"等待页面元素超时: {e}"
        except Exception as e:
            logger.error(f"账号 {self.account_id} 发送验证码失败: {e}")
            return False, str(e)

    async def submit_verification_code(self, code: str) -> Tuple[bool, str]:
        """
        提交验证码完成登录
        - 输入6位验证码
        - 点击登录按钮
        - 检测登录结果
        """
        try:
            if not self.page:
                return False, "页面未初始化，请先调用 login_with_sms"

            logger.info(f"账号 {self.account_id} 提交验证码: {code[:2]}**")

            # 查找验证码输入框
            code_input = None
            for selector in LOGIN_SELECTORS["code_input"]:
                try:
                    code_input = await self.page.wait_for_selector(selector, timeout=3000)
                    if code_input:
                        logger.debug(f"找到验证码输入框: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not code_input:
                await self.page.screenshot(path=f"logs/code_input_debug_{self.account_id}.png")
                return False, "未找到验证码输入框"

            # 输入验证码
            await code_input.fill(code)
            await self.page.wait_for_timeout(500)

            # 查找登录按钮
            login_button = None
            for selector in LOGIN_SELECTORS["login_button"]:
                try:
                    login_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if login_button:
                        logger.debug(f"找到登录按钮: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if not login_button:
                await self.page.screenshot(path=f"logs/login_btn_debug_{self.account_id}.png")
                return False, "未找到登录按钮"

            # 点击登录
            await login_button.click()
            await self.page.wait_for_timeout(2000)  # 等待登录响应

            # 检测登录结果
            success, message = await self._check_login_result()
            if success:
                self.logged_in = True
                logger.info(f"账号 {self.account_id} 登录成功")
            else:
                logger.warning(f"账号 {self.account_id} 登录失败: {message}")

            return success, message

        except PlaywrightTimeout as e:
            logger.error(f"账号 {self.account_id} 等待元素超时: {e}")
            return False, f"等待页面元素超时: {e}"
        except Exception as e:
            logger.error(f"账号 {self.account_id} 提交验证码失败: {e}")
            return False, str(e)

    async def _check_login_result(self) -> Tuple[bool, str]:
        """检查登录结果"""
        try:
            # 检查是否跳转到主页
            await self.page.wait_for_timeout(2000)

            current_url = self.page.url
            logger.debug(f"当前URL: {current_url}")

            # 如果URL不包含login，认为登录成功
            if "login" not in current_url.lower():
                return True, "登录成功"

            # 检查页面是否有登录成功的标识
            for selector in LOGIN_SELECTORS["logged_in_indicator"]:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        return True, "登录成功"
                except PlaywrightTimeout:
                    continue

            # 检查是否有错误提示
            error_selectors = [
                '[class*="error"]',
                '[class*="wrong"]',
                '[class*="fail"]',
                '.toast:has-text("错误")',
                '.message:has-text("失败")',
            ]
            for selector in error_selectors:
                try:
                    error_el = await self.page.wait_for_selector(selector, timeout=1000)
                    if error_el:
                        error_text = await error_el.text_content()
                        return False, f"登录错误: {error_text}"
                except PlaywrightTimeout:
                    continue

            return False, "登录状态未知，请检查页面"

        except Exception as e:
            logger.error(f"检查登录结果失败: {e}")
            return False, str(e)

    async def is_logged_in(self) -> bool:
        """
        检测是否已登录
        通过访问主页检查是否跳转到登录页
        """
        try:
            if not self.page:
                return False

            # 访问主页
            await self.page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(1000)

            current_url = self.page.url

            # 如果URL包含login，说明未登录
            if "login" in current_url.lower():
                return False

            # 检查登录标识
            for selector in LOGIN_SELECTORS["logged_in_indicator"]:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        return True
                except PlaywrightTimeout:
                    continue

            # 如果URL不包含login，认为已登录
            return "login" not in current_url.lower()

        except Exception as e:
            logger.error(f"检测登录状态失败: {e}")
            return False

    async def wait_for_login(self, timeout: int = 300000) -> Tuple[bool, str]:
        """
        等待登录完成（用于扫码登录场景）
        - 等待用户扫码
        - 超时时间默认5分钟
        """
        try:
            if not self.page:
                self.page = await browser_manager.new_page(self.account_id)
                if not self.page:
                    return False, "创建浏览器页面失败"

            logger.info(f"账号 {self.account_id} 等待登录 (超时: {timeout}ms)")

            # 确保在登录页面
            if "login" not in self.page.url.lower():
                await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded")

            # 等待登录成功标识出现
            start_time = asyncio.get_event_loop().time()

            for selector in LOGIN_SELECTORS["logged_in_indicator"]:
                try:
                    element = await self.page.wait_for_selector(
                        selector,
                        timeout=timeout
                    )
                    if element:
                        self.logged_in = True
                        logger.info(f"账号 {self.account_id} 登录成功（检测到用户信息）")
                        return True, "登录成功"
                except PlaywrightTimeout:
                    continue

            # 备用方案：检查URL变化
            remaining_time = timeout - int((asyncio.get_event_loop().time() - start_time) * 1000)
            if remaining_time > 0:
                try:
                    await self.page.wait_for_url(
                        lambda url: "login" not in url.lower(),
                        timeout=remaining_time
                    )
                    self.logged_in = True
                    return True, "登录成功"
                except PlaywrightTimeout:
                    pass

            return False, "登录超时"

        except Exception as e:
            logger.error(f"账号 {self.account_id} 等待登录失败: {e}")
            return False, str(e)

    async def explore_login_page(self) -> Dict[str, Any]:
        """
        探索登录页面元素（调试用）
        返回所有找到的元素信息
        """
        try:
            if not self.page:
                self.page = await browser_manager.new_page(self.account_id)
                if not self.page:
                    return {"error": "创建页面失败"}

            await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(3000)

            result = {"url": self.page.url, "elements": {}}

            # 遍历所有选择器
            for category, selectors in LOGIN_SELECTORS.items():
                found = []
                for selector in selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if elements:
                            found.append({
                                "selector": selector,
                                "count": len(elements),
                                "html": await elements[0].evaluate("el => el.outerHTML[:200]")
                            })
                    except Exception:
                        continue
                result["elements"][category] = found

            # 页面HTML片段
            result["page_info"] = await self.page.evaluate("""
                () => {
                    const inputs = document.querySelectorAll('input');
                    const buttons = document.querySelectorAll('button');
                    return {
                        input_count: inputs.length,
                        button_count: buttons.length,
                        title: document.title,
                        h1: document.querySelector('h1')?.textContent || '',
                    };
                }
            """)

            # 保存截图
            await self.page.screenshot(path=f"logs/login_explore_{self.account_id}.png")
            result["screenshot"] = f"logs/login_explore_{self.account_id}.png"

            logger.info(f"账号 {self.account_id} 登录页面探索完成")
            return result

        except Exception as e:
            logger.error(f"探索登录页面失败: {e}")
            return {"error": str(e)}

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

            # 检查登录标识
            for selector in LOGIN_SELECTORS["logged_in_indicator"]:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        self.logged_in = True
                        return True, "已登录"
                except PlaywrightTimeout:
                    continue

            self.logged_in = "login" not in self.page.url.lower()
            return (True, "已登录") if self.logged_in else (False, "未登录")

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
            logger.info("登录页面截图已保存: path={}", path)

    async def login_with_sms(self, phone: str, code: str) -> Tuple[bool, str]:
        """
        通过手机验证码登录（一步完成）
        - 打开登录页
        - 勾选协议
        - 输入手机号
        - 点击发送验证码
        - 输入验证码
        - 点击登录
        - 检测登录结果
        - 返回登录状态

        Args:
            phone: 手机号（11位）
            code: 验证码（4-6位）

        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 创建新页面或使用现有页面
            if not self.page:
                self.page = await browser_manager.new_page(self.account_id)
                if not self.page:
                    return False, "创建浏览器页面失败"

            logger.info("账号 {} 开始手机登录", self.account_id)

            # 访问登录页面
            await self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(2000)  # 等待页面完全加载

            # 保存调试截图
            await self._save_debug_screenshot("login_start")

            # ========== 第一步：勾选协议复选框 ==========
            checkbox_selected = await self._select_agree_checkbox()
            if not checkbox_selected:
                logger.warning("账号 {} 未勾选协议或未找到复选框", self.account_id)

            # ========== 第二步：输入手机号 ==========
            phone_input = await self._find_element(self.page, LOGIN_SELECTORS["phone_input"])
            if not phone_input:
                await self._save_debug_screenshot("phone_input_not_found")
                return False, "未找到手机号输入框"

            await phone_input.fill(phone)
            await self.page.wait_for_timeout(500)
            logger.debug("账号 {} 手机号已输入: {}***", self.account_id, phone[:3])

            # ========== 第三步：点击发送验证码 ==========
            code_button = await self._find_element(self.page, LOGIN_SELECTORS["code_button"])
            if not code_button:
                await self._save_debug_screenshot("code_button_not_found")
                return False, "未找到验证码按钮"

            await code_button.click()
            logger.info("账号 {} 验证码已发送", self.account_id)
            await self.page.wait_for_timeout(1000)

            # ========== 第四步：输入验证码 ==========
            code_input = await self._find_element(self.page, LOGIN_SELECTORS["code_input"])
            if not code_input:
                await self._save_debug_screenshot("code_input_not_found")
                return False, "未找到验证码输入框"

            await code_input.fill(code)
            await self.page.wait_for_timeout(500)
            logger.debug("账号 {} 验证码已输入: {}**", self.account_id, code[:2])

            # ========== 第五步：点击登录按钮 ==========
            login_button = await self._find_element(self.page, LOGIN_SELECTORS["login_button"])
            if not login_button:
                await self._save_debug_screenshot("login_button_not_found")
                return False, "未找到登录按钮"

            await login_button.click()
            logger.info("账号 {} 点击登录按钮", self.account_id)
            await self.page.wait_for_timeout(3000)  # 等待登录响应

            # ========== 第六步：检测登录结果 ==========
            success, message = await self._check_login_result()

            if success:
                self.logged_in = True
                logger.info("账号 {} 登录成功", self.account_id)
            else:
                logger.warning("账号 {} 登录失败: {}", self.account_id, message)
                await self._save_debug_screenshot("login_failed")

            return success, message

        except PlaywrightTimeout as e:
            logger.error("账号 {} 等待元素超时: {}", self.account_id, e)
            await self._save_debug_screenshot("login_timeout")
            return False, f"等待页面元素超时: {e}"
        except Exception as e:
            logger.error("账号 {} 登录过程异常: {}", self.account_id, e, exc_info=True)
            return False, str(e)

    async def _select_agree_checkbox(self) -> bool:
        """勾选同意协议复选框"""
        for selector in LOGIN_SELECTORS["agree_checkbox"]:
            try:
                checkbox = await self.page.wait_for_selector(selector, timeout=2000)
                if checkbox:
                    is_checked = await checkbox.is_checked()
                    if not is_checked:
                        await checkbox.check()
                        logger.debug("已勾选协议复选框: {}", selector)
                    return True
            except PlaywrightTimeout:
                continue
        return False

    async def _find_element(self, page: Page, selectors: list) -> Optional[Any]:
        """查找页面元素"""
        for selector in selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    logger.debug("找到元素: {}", selector)
                    return element
            except PlaywrightTimeout:
                continue
        return None

    async def _save_debug_screenshot(self, prefix: str) -> None:
        """保存调试截图"""
        try:
            path = f"logs/debug_{prefix}_{self.account_id}.png"
            if self.page:
                await self.page.screenshot(path=path)
                logger.debug("调试截图已保存: {}", path)
        except Exception as e:
            logger.warning("保存调试截图失败: {}", e)

    async def save_login_session(self) -> Optional[str]:
        """
        保存登录会话
        返回加密后的 storage state

        Returns:
            Optional[str]: 加密后的 storage state，失败返回 None
        """
        try:
            storage_state = await browser_manager.save_storage_state(self.account_id)
            if storage_state:
                logger.info("账号 {} 登录会话已保存", self.account_id)
                return storage_state
            else:
                logger.warning("账号 {} 保存登录会话失败", self.account_id)
                return None
        except Exception as e:
            logger.error("账号 {} 保存登录会话异常: {}", self.account_id, e, exc_info=True)
            return None

    async def load_login_session(self, storage_state: str) -> bool:
        """
        加载已保存的登录会话

        Args:
            storage_state: 加密后的 storage state

        Returns:
            bool: 加载是否成功
        """
        try:
            # 创建新上下文并加载 storage state
            context = await browser_manager.create_context(self.account_id, storage_state)
            if context:
                # 创建新页面
                self.page = await context.new_page()
                logger.info("账号 {} 登录会话已加载", self.account_id)
                return True
            return False
        except Exception as e:
            logger.error("账号 {} 加载登录会话异常: {}", self.account_id, e, exc_info=True)
            return False

    async def close(self):
        """关闭客户端"""
        if self.page:
            await self.page.close()
            self.page = None
            self.logged_in = False


async def get_dewu_client(account_id: int) -> DewuClient:
    """获取得物客户端"""
    return DewuClient(account_id)
