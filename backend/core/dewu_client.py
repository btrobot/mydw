"""
得物掘金工具 - 得物平台客户端
"""
import asyncio
from typing import Optional, Tuple, Dict, Any, List
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

            logger.info("账号 {} 开始登录得物", self.account_id)

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
                logger.info("账号 {} 登录成功", self.account_id)
                return True, "登录成功"

            except Exception:
                # 可能是二维码过期或其他问题
                return False, "登录超时或失败"

        except Exception as e:
            logger.error("账号 {} 登录失败: {}", self.account_id, e)
            return False, str(e)

    async def _check_login_result(self) -> Tuple[bool, str]:
        """检查登录结果"""
        try:
            # 检查是否跳转到主页
            await self.page.wait_for_timeout(2000)

            current_url = self.page.url
            logger.debug("当前URL: {}", current_url)

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
            logger.error("检查登录结果失败: {}", e)
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
            logger.error("检测登录状态失败: {}", e)
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

            logger.info("账号 {} 等待登录 (超时: {}ms)", self.account_id, timeout)

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
                        logger.info("账号 {} 登录成功（检测到用户信息）", self.account_id)
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
            logger.error("账号 {} 等待登录失败: {}", self.account_id, e)
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

            logger.info("账号 {} 登录页面探索完成", self.account_id)
            return result

        except Exception as e:
            logger.error("探索登录页面失败: {}", e)
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
            logger.error("检查登录状态失败: {}", e)
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
            logger.error("获取用户信息失败: {}", e)
            return None

    async def scrape_profile(self) -> Optional[Dict[str, str]]:
        """
        登录成功后抓取用户 profile 信息。

        前提：login 已成功，self.page 处于已登录状态。

        Returns:
            Optional[Dict]: {"nickname": "...", "uid": "...", "avatar_url": "..."}
            失败返回 None（不影响登录流程）
        """
        async def _do_scrape() -> Optional[Dict[str, str]]:
            # 前提检查：page 必须存在且不处于登录页
            if not self.page:
                logger.warning("账号 {} scrape_profile: page 不存在", self.account_id)
                return None

            current_url = self.page.url
            if "login" in current_url.lower():
                logger.warning("账号 {} scrape_profile: 当前页面仍在登录页 url={}", self.account_id, current_url)
                return None

            # 第一步：从当前页面 DOM 提取信息
            profile: Dict[str, Optional[str]] = await self.page.evaluate("""
                () => {
                    // 昵称：多选择器尝试
                    const nicknameSelectors = [
                        '.user-name',
                        '.nickname',
                        '[class*="user-name"]',
                        '[class*="nickname"]',
                        '[class*="header-user"] [class*="name"]',
                        'header [class*="user"] [class*="name"]',
                        'nav [class*="user"] span',
                    ];
                    let nickname = null;
                    for (const sel of nicknameSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.textContent && el.textContent.trim()) {
                            nickname = el.textContent.trim();
                            break;
                        }
                    }

                    // 头像：导航栏区域 img
                    const avatarSelectors = [
                        'header [class*="avatar"] img',
                        'nav [class*="avatar"] img',
                        '[class*="header-user"] img',
                        '[class*="user-avatar"] img',
                        '.user-avatar img',
                    ];
                    let avatar_url = null;
                    for (const sel of avatarSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.src) {
                            avatar_url = el.src;
                            break;
                        }
                    }

                    // UID：从页面元素或 URL 中尝试提取
                    const uidSelectors = [
                        '[class*="uid"]',
                        '[class*="user-id"]',
                        '[data-uid]',
                        '[data-user-id]',
                    ];
                    let uid = null;
                    for (const sel of uidSelectors) {
                        const el = document.querySelector(sel);
                        if (el) {
                            uid = el.getAttribute('data-uid') ||
                                  el.getAttribute('data-user-id') ||
                                  (el.textContent && el.textContent.trim()) ||
                                  null;
                            if (uid) break;
                        }
                    }
                    // UID 备用：从当前 URL 路径段中匹配纯数字
                    if (!uid) {
                        const parts = window.location.pathname.split('/');
                        for (const part of parts) {
                            if (/^\\d{5,}$/.test(part)) {
                                uid = part;
                                break;
                            }
                        }
                    }

                    return { nickname, uid, avatar_url };
                }
            """)

            # 判断当前页面信息是否足够
            has_info = profile.get("nickname") or profile.get("uid")
            if has_info:
                logger.info(
                    "账号 {} scrape_profile 成功（当前页面）: nickname_found={} uid_found={}",
                    self.account_id,
                    bool(profile.get("nickname")),
                    bool(profile.get("uid")),
                )
                return {k: v for k, v in profile.items()}

            # 第二步：当前页面信息不足，在新 tab 中访问个人中心
            logger.info("账号 {} scrape_profile: 当前页面信息不足，尝试新 tab", self.account_id)
            new_page = None
            try:
                context = self.page.context
                new_page = await context.new_page()
                await new_page.goto(
                    f"{self.BASE_URL}/user/profile",
                    wait_until="domcontentloaded",
                    timeout=8000,
                )
                await new_page.wait_for_timeout(1500)

                profile2: Dict[str, Optional[str]] = await new_page.evaluate("""
                    () => {
                        const nicknameSelectors = [
                            '.user-name',
                            '.nickname',
                            '[class*="user-name"]',
                            '[class*="nickname"]',
                            '[class*="profile"] [class*="name"]',
                        ];
                        let nickname = null;
                        for (const sel of nicknameSelectors) {
                            const el = document.querySelector(sel);
                            if (el && el.textContent && el.textContent.trim()) {
                                nickname = el.textContent.trim();
                                break;
                            }
                        }

                        const avatarSelectors = [
                            '[class*="avatar"] img',
                            '[class*="profile"] img',
                            '.user-avatar img',
                        ];
                        let avatar_url = null;
                        for (const sel of avatarSelectors) {
                            const el = document.querySelector(sel);
                            if (el && el.src) {
                                avatar_url = el.src;
                                break;
                            }
                        }

                        let uid = null;
                        const uidSelectors = ['[class*="uid"]', '[data-uid]', '[data-user-id]'];
                        for (const sel of uidSelectors) {
                            const el = document.querySelector(sel);
                            if (el) {
                                uid = el.getAttribute('data-uid') ||
                                      el.getAttribute('data-user-id') ||
                                      (el.textContent && el.textContent.trim()) ||
                                      null;
                                if (uid) break;
                            }
                        }
                        if (!uid) {
                            const parts = window.location.pathname.split('/');
                            for (const part of parts) {
                                if (/^\\d{5,}$/.test(part)) {
                                    uid = part;
                                    break;
                                }
                            }
                        }

                        return { nickname, uid, avatar_url };
                    }
                """)
                logger.info(
                    "账号 {} scrape_profile 成功（新 tab）: nickname_found={} uid_found={}",
                    self.account_id,
                    bool(profile2.get("nickname")),
                    bool(profile2.get("uid")),
                )
                return {k: v for k, v in profile2.items()}
            finally:
                if new_page:
                    try:
                        await new_page.close()
                    except Exception:
                        pass

        try:
            result = await asyncio.wait_for(_do_scrape(), timeout=10.0)
            return result
        except asyncio.TimeoutError:
            logger.warning("账号 {} scrape_profile 超时（10s）", self.account_id)
            return None
        except Exception as e:
            logger.warning("账号 {} scrape_profile 异常: error_type={}", self.account_id, type(e).__name__)
            return None

    async def upload_video(self, video_path: str, title: str, content: str,
                          topic: str = "", cover_path: Optional[str] = None,
                          product_link: Optional[str] = None) -> Tuple[bool, str]:
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

            logger.info("账号 {} 视频上传中: {}", self.account_id, video_path)

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

            # 填入商品链接
            if product_link:
                try:
                    product_input = await self.page.wait_for_selector(
                        'input[class*="product"], input[placeholder*="商品"], input[placeholder*="链接"]',
                        timeout=5000
                    )
                    await product_input.fill(product_link)
                    logger.info("账号 {} 已填入商品链接", self.account_id)
                except Exception as e:
                    logger.warning("账号 {} 填入商品链接失败: {}", self.account_id, e)

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

            logger.info("账号 {} 视频发布成功", self.account_id)
            return True, "发布成功"

        except Exception as e:
            logger.error("账号 {} 视频发布失败: {}", self.account_id, e)
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
            logger.error("获取统计数据失败: {}", e)
            return None

    async def screenshot_login(self, path: str = "logs/login.png"):
        """截取登录页面"""
        if self.page:
            await self.page.screenshot(path=path, full_page=True)
            logger.info("登录页面截图已保存: path={}", path)

    async def send_sms_code(self, phone: str) -> Tuple[bool, str]:
        """
        第一阶段：打开登录页，输入手机号，点击发送验证码

        self.page 保持打开状态，供 verify_sms_code 使用。

        Args:
            phone: 手机号（11位）

        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 创建新页面或使用现有页面
            if not self.page:
                self.page = await browser_manager.new_page(self.account_id)
                if not self.page:
                    return False, "创建浏览器页面失败"

            logger.info("账号 {} 开始手机登录第一阶段：发送验证码", self.account_id)

            # 访问登录页面
            await self.page.goto(self.LOGIN_URL, wait_until="networkidle", timeout=60000)
            await self.page.wait_for_timeout(2000)  # 等待页面完全加载

            # 保存调试截图
            await self._save_debug_screenshot("login_start")

            # ========== 第一步：勾选协议复选框（移到手机号输入之前，与 test_patch_login_debug.py 一致）==========
            checkbox_selected = await self._select_agree_checkbox()
            if not checkbox_selected:
                logger.warning("账号 {} 未勾选协议或未找到复选框，可能协议已默认勾选", self.account_id)

            # ========== 第二步：输入手机号 ==========
            phone_input = await self._find_element(self.page, LOGIN_SELECTORS["phone_input"])
            if not phone_input:
                await self._save_debug_screenshot("phone_input_not_found")
                return False, "未找到手机号输入框"

            await phone_input.fill(phone)
            await self.page.wait_for_timeout(500)
            logger.debug("账号 {} 手机号已输入: {}***", self.account_id, phone[:3])

            # ========== 第三步：点击发送验证码（使用文本遍历查找，与 test_patch_login_debug.py 一致）==========
            # 使用文本遍历查找验证码按钮
            code_button = await self._find_button_by_text(
                self.page,
                ['验证码', '发送', '获取']
            )
            if not code_button:
                # 备用：尝试选择器
                code_button = await self._find_element(self.page, LOGIN_SELECTORS["code_button"])

            if not code_button:
                await self._save_debug_screenshot("code_button_not_found")
                return False, "未找到验证码按钮"

            await code_button.click()
            logger.info("账号 {} 验证码已发送", self.account_id)
            await self.page.wait_for_timeout(2000)  # 等待验证码发送完成

            # 保存发送验证码后的截图
            await self._save_debug_screenshot("after_code_sent")

            return True, "验证码已发送"

        except PlaywrightTimeout as e:
            logger.error("账号 {} 发送验证码等待元素超时: {}", self.account_id, e)
            await self._save_debug_screenshot("send_code_timeout")
            return False, f"等待页面元素超时: {e}"
        except Exception as e:
            logger.error("账号 {} 发送验证码过程异常: {}", self.account_id, e, exc_info=True)
            return False, str(e)

    async def verify_sms_code(self, code: str) -> Tuple[bool, str]:
        """
        第二阶段：输入验证码，点击登录，检测登录结果

        前提：send_sms_code 已成功执行，self.page 持有登录页实例。

        Args:
            code: 短信验证码（4-6位）

        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        try:
            # 前提检查：self.page 必须是 send_sms_code 遗留的登录页
            if not self.page:
                return False, "没有活跃的登录页面，请先调用 send_sms_code"

            logger.info("账号 {} 开始手机登录第二阶段：验证码登录", self.account_id)

            # ========== 第四步：输入验证码 ==========
            code_input = await self._find_element(self.page, LOGIN_SELECTORS["code_input"])
            if not code_input:
                await self._save_debug_screenshot("code_input_not_found")
                return False, "未找到验证码输入框"

            await code_input.fill(code)
            await self.page.wait_for_timeout(500)
            logger.debug("账号 {} 验证码已输入: {}**", self.account_id, code[:2])

            # ========== 第五步：点击登录按钮 ==========
            # 尝试多个可能的登录按钮选择器
            login_button = await self._find_element_with_fallback(
                self.page,
                LOGIN_SELECTORS["login_button"],
                ['button:has-text("登录")', 'button[type="submit"]']
            )
            if not login_button:
                await self._save_debug_screenshot("login_button_not_found")
                return False, "未找到登录按钮"

            await login_button.click()
            logger.info("账号 {} 点击登录按钮", self.account_id)
            await self.page.wait_for_timeout(3000)  # 等待登录响应

            # 保存登录后的截图
            await self._save_debug_screenshot("after_login_click")

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
            logger.error("账号 {} 验证码登录等待元素超时: {}", self.account_id, e)
            await self._save_debug_screenshot("verify_code_timeout")
            return False, f"等待页面元素超时: {e}"
        except Exception as e:
            logger.error("账号 {} 验证码登录过程异常: {}", self.account_id, e, exc_info=True)
            return False, str(e)

    async def login_with_sms(self, phone: str, code: str) -> Tuple[bool, str]:
        """
        通过手机验证码登录（兼容包装，内部依次调用 send_sms_code + verify_sms_code）

        Args:
            phone: 手机号（11位）
            code: 验证码（4-6位）

        Returns:
            Tuple[bool, str]: (成功标志, 消息)
        """
        send_success, send_message = await self.send_sms_code(phone)
        if not send_success:
            return False, send_message

        return await self.verify_sms_code(code)

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

    async def _find_button_by_text(self, page: Page, patterns: List[str]) -> Optional[Any]:
        """
        根据文本内容查找按钮（与 test_patch_login_debug.py 一致的逻辑）

        Args:
            page: Playwright 页面对象
            patterns: 要匹配的文本模式列表

        Returns:
            找到的按钮元素，未找到返回 None
        """
        buttons = await page.query_selector_all('button')
        for btn in buttons:
            text = await btn.text_content()
            if text:
                text_lower = text.lower()
                for pattern in patterns:
                    if pattern.lower() in text_lower:
                        logger.debug("找到按钮: pattern={}, text={}", pattern, text.strip())
                        return btn
        return None

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

    async def _find_element_with_fallback(
        self, page: Page, primary_selectors: list, fallback_selectors: list
    ) -> Optional[Any]:
        """
        查找页面元素，优先使用主选择器，失败后使用备用选择器

        Args:
            page: Playwright 页面对象
            primary_selectors: 主选择器列表
            fallback_selectors: 备用选择器列表

        Returns:
            找到的元素，未找到返回 None
        """
        # 首先尝试主选择器
        element = await self._find_element(page, primary_selectors)
        if element:
            return element

        # 主选择器失败，尝试备用选择器
        logger.debug("主选择器未找到，尝试备用选择器")
        element = await self._find_element(page, fallback_selectors)
        if element:
            return element

        # 所有选择器都失败
        logger.warning("所有选择器都未找到元素: primary={}, fallback={}", primary_selectors, fallback_selectors)
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


# ========== 模块级实例管理 ==========

_active_clients: Dict[int, DewuClient] = {}


async def get_or_create_client(account_id: int) -> DewuClient:
    """
    获取或创建指定账号的 DewuClient 实例

    两阶段登录流程（send_sms_code / verify_sms_code）期间，
    浏览器实例必须在两次调用之间保持存活。
    使用此函数确保同一账号复用同一实例。

    Args:
        account_id: 账号数据库主键 ID

    Returns:
        DewuClient: 该账号的客户端实例
    """
    if account_id not in _active_clients:
        _active_clients[account_id] = DewuClient(account_id)
    return _active_clients[account_id]


def release_client(account_id: int) -> None:
    """
    释放并移除指定账号的 DewuClient 实例

    在登录流程结束（成功或失败）后调用，避免僵尸浏览器实例。

    Args:
        account_id: 账号数据库主键 ID
    """
    _active_clients.pop(account_id, None)
