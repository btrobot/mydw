# 得物登录自动化技术方案

> 文档日期: 2026-04-02
> 状态: 已解决

## 背景

得物创作者平台 (creator.dewu.com) 部署了反爬虫/反自动化检测机制。我们需要实现自动登录功能。

## 探索历程

### 第一阶段: Playwright 尝试

#### 1.1 基础 Playwright

**尝试**: 使用标准 Playwright 打开登录页

```python
from playwright.async_api import async_playwright

async with async_playwright() as pw:
    browser = await pw.chromium.launch()
    page = await browser.new_page()
    await page.goto('https://creator.dewu.com/login')
```

**结果**: ❌ 页面显示 "环境异常"，被检测为自动化浏览器

#### 1.2 playwright-stealth 库

**尝试**: 安装并使用 `playwright-stealth` 库

```python
from playwright_stealth import stealth_async

page = await context.new_page()
await stealth_async(page)
```

**结果**: ❌ 仍然显示"环境异常"

#### 1.3 自定义反检测脚本

**尝试**: 添加 JavaScript 脚本隐藏自动化特征

```python
await page.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    // ... 更多伪装代码
""")
```

**结果**: ❌ 仍然被检测

#### 1.4 更多浏览器参数

**尝试**: 添加更多 Chrome 启动参数

```python
args=[
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-web-security',
    '--disable-features=IsolateOrigins,site-per-process',
    '--disable-gpu',
    '--single-process',
]
```

**结果**: ❌ 无效

---

### 第二阶段: 第三方框架探索

#### 2.1 Scrapling 框架

**发现**: Scrapling 是一个带反检测的爬虫框架

```python
from scrapling.fetchers import StealthyFetcher, DynamicFetcher
```

**问题**:
- `StealthyFetcher` 是静态爬虫，无法进行浏览器交互
- `DynamicFetcher` 仍然基于 Playwright，同样被检测
- API 设计不适合我们的使用场景

**结果**: ❌ 不适合

---

### 第三阶段: Patchright 突破

#### 3.1 发现 Patchright

**发现**: Patchright 是 Playwright 的反检测分支，专门为绕过 bot 检测设计

**安装**:
```bash
pip install patchright -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 3.2 首次成功

**测试代码**:
```python
from patchright.async_api import async_playwright

async with async_playwright() as pw:
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        locale='zh-CN',
    )
    page = await context.new_page()
    await page.goto('https://creator.dewu.com/login')
    await page.screenshot(path='test.png')
```

**结果**: ✅ **成功绕过检测！页面正常显示！**

---

## 最终方案

### 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 浏览器 | Patchright | 专门反检测，已验证可用 |
| API 风格 | Async | 与 FastAPI 异步架构匹配 |

### 项目配置

#### 依赖安装

```bash
# 使用清华镜像
pip install patchright -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 Chromium 浏览器
patchright install chromium
```

#### browser.py 核心代码

```python
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
        self.contexts: Dict[int, any] = {}
        self._lock = asyncio.Lock()

    async def init(self):
        """初始化 Patchright 浏览器"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
            )
            logger.info(f"Patchright 浏览器已启动")

    async def new_page(self, account_id: int):
        """为账号创建新页面"""
        context = await self.get_or_create_context(account_id)
        if context:
            page = await context.new_page()
            return page
        return None
```

### 登录页面元素选择器

```python
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
    ],
    "code_input": [
        'input[placeholder*="验证码"]',
    ],
    # 重要：使用 "登 录"（有空格），避免误点 "密码登录"
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
}
```

### 关键发现

| 发现 | 说明 |
|------|------|
| **登录按钮文本** | 是 "登 录"（中间有空格），不是 "登录" |
| **误点问题** | "密码登录" 按钮会误匹配 |
| **登录成功判断** | URL 跳转到非 login 页面即为成功 |
| **成功跳转页面** | 跳转到 `/release` 或 `/content` 等 |
```

### 完整登录流程

```python
async def login_with_sms(phone: str, code: str) -> Tuple[bool, str]:
    """通过手机验证码登录"""

    # 1. 打开登录页
    page = await browser_manager.new_page(account_id)

    # 2. 勾选协议
    checkbox = await page.query_selector('input[type="checkbox"]')
    await checkbox.check()

    # 3. 输入手机号
    phone_input = await page.query_selector('input[placeholder*="手机"]')
    await phone_input.fill(phone)

    # 4. 点击发送验证码
    code_button = await page.query_selector('button:has-text("发送验证码")')
    await code_button.click()

    # 5. 等待验证码输入（可通过 API 接收）
    # await asyncio.sleep(30)  # 等待用户输入

    # 6. 输入验证码
    code_input = await page.query_selector('input[placeholder*="验证码"]')
    await code_input.fill(code)

    # 7. 点击登录
    login_button = await page.query_selector('button:has-text("登录")')
    await login_button.click()

    # 8. 保存登录状态
    storage_state = await browser_manager.save_storage_state(account_id)

    return True, "登录成功"
```

---

## 测试脚本

### 基础测试

```python
# test_patchright.py
import asyncio
from patchright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('https://creator.dewu.com/login')
        await page.screenshot(path='logs/test.png')
        input("按回车关闭...")

asyncio.run(main())
```

### 完整登录测试

```python
# test_patch_login.py
import asyncio
from patchright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()

        # 打开登录页
        await page.goto('https://creator.dewu.com/login')

        # 勾选协议
        checkbox = await page.query_selector('input[type="checkbox"]')
        await checkbox.check()

        # 输入手机号
        phone = input("手机号: ")
        await page.fill('input[placeholder*="手机"]', phone)

        # 发送验证码
        await page.click('button:has-text("发送验证码")')

        # 输入验证码
        code = input("验证码: ")
        await page.fill('input[placeholder*="验证码"]', code)

        # 登录
        await page.click('button:has-text("登录")')

        input("按回车关闭...")

asyncio.run(main())
```

---

## 已知问题与注意事项

### 1. 验证码频率限制

得物有验证码发送频率限制：
- 同一手机号短时间内多次请求会被限制
- 提示: "获取验证码频繁操作，请稍后再试"
- 解决: 等待 5-10 分钟后重试

### 2. Session 持久化

登录成功后应立即保存 storage state：
```python
state = await context.storage_state()
encrypted = encrypt_data(json.dumps(state))
# 保存到数据库
```

### 3. 多账号隔离

每个账号使用独立的 BrowserContext：
```python
contexts = {}  # account_id -> context
```

---

## 技术对比

| 方案 | 反检测 | 维护状态 | 适用场景 |
|------|--------|----------|----------|
| Playwright | ❌ | 活跃 | 普通网站 |
| playwright-stealth | ⚠️ | 低维护 | 部分网站 |
| undetected-chromedriver | ✅ | 活跃 | Selenium 用户 |
| **Patchright** | ✅✅ | 活跃 | Playwright 用户 |
| Scraping + Stealth | ⚠️ | 活跃 | 静态爬虫 |

---

## 相关文件

```
backend/
├── core/
│   ├── browser.py          # Patchright 浏览器管理
│   └── dewu_client.py     # 得物客户端
├── test_patchright.py     # 基础测试
├── test_patch_login.py    # 登录流程测试
└── test_debug_page.py     # 页面结构调试
```

---

## 附录: 安装命令

```powershell
# 进入后端目录
cd backend

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 安装 patchright（清华镜像）
.\venv\Scripts\pip.exe install patchright -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 chromium 浏览器
.\venv\Scripts\python.exe -m patchright install chromium
```

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-04-02 | v1.0 | 初始文档 |
| 2026-04-02 | v1.1 | 添加完整登录流程代码 |
