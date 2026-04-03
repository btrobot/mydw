"""
得物登录页面元素探索脚本 - 最终版
基于常见登录页面模式提供推荐选择器
"""
import asyncio
from playwright.async_api import async_playwright


# 常见的登录页面元素选择器模式
# 这些选择器基于常见的登录页面设计，实际使用时需要验证

COMMON_SELECTORS = {
    # 手机号输入框
    "phone_input": [
        'input[placeholder*="手机"]',
        'input[placeholder*="phone"]',
        'input[placeholder*="Phone"]',
        'input[placeholder*="手机号"]',
        'input[name="phone"]',
        'input[name="mobile"]',
        'input[id*="phone"]',
        'input[class*="phone"]',
        'input[type="tel"]',
        'input[autocomplete="tel"]',
    ],

    # 验证码输入框
    "code_input": [
        'input[placeholder*="验证码"]',
        'input[placeholder*="码"]',
        'input[placeholder*="code"]',
        'input[placeholder*="Code"]',
        'input[name="code"]',
        'input[name="captcha"]',
        'input[id*="code"]',
        'input[class*="code"]',
    ],

    # 获取验证码按钮
    "send_code_button": [
        'button:has-text("获取验证码")',
        'button:has-text("发送验证码")',
        'button:has-text("发送")',
        'button:has-text("获取")',
        'button[class*="send"]',
        'button[class*="code"]',
        'span:has-text("获取验证码")',
        'a:has-text("获取验证码")',
    ],

    # 登录/提交按钮
    "login_button": [
        'button:has-text("登录")',
        'button:has-text("登 录")',
        'button[type="submit"]',
        'button[class*="login"]',
        'button[class*="submit"]',
        'button:has-text("确认")',
    ],

    # 登录方式切换
    "login_tab": [
        'div:has-text("验证码登录")',
        'div:has-text("密码登录")',
        'span:has-text("验证码登录")',
        'span:has-text("密码登录")',
        '[class*="tab"]:has-text("验证码")',
        '[role="tab"]:has-text("验证码")',
    ],

    # 登录成功标志
    "login_success": [
        '[class*="user"]',
        '[class*="avatar"]',
        '[class*="nickname"]',
        '[class*="username"]',
        '[class*="profile"]',
        '[class*="info"]',
    ],

    # 错误提示
    "error_message": [
        '[class*="error"]',
        '[class*="Error"]',
        '[class*="warning"]',
        '[class*="alert"]',
        '[class*="message"]',
    ],
}


async def explore_login_page():
    """探索登录页面并测试选择器"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        page = await context.new_page()

        print("=" * 60)
        print("得物登录页面选择器探索工具")
        print("=" * 60)

        try:
            # 访问登录页面
            print("\n正在访问登录页面...")
            await page.goto("https://creator.dewu.com/passport/login", timeout=30000)
            print(f"URL: {page.url}")

            # 等待加载
            await asyncio.sleep(3)
            await page.screenshot(path="login_page_raw.png")

            print("\n测试各种选择器...")
            print()

            results = {}

            for category, selectors in COMMON_SELECTORS.items():
                print(f"--- {category} ---")
                found = []

                for selector in selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        visible_elements = [el for el in elements if await el.is_visible()]
                        if visible_elements:
                            for el in visible_elements[:2]:  # 只显示前2个
                                if "input" in selector:
                                    info = await el.get_attribute("placeholder") or ""
                                else:
                                    info = (await el.inner_text()).strip()[:30]
                                found.append(f"  {selector} -> {info}")
                    except Exception:
                        pass

                if found:
                    results[category] = found
                    for f in found:
                        print(f)
                else:
                    print("  (未找到)")
                print()

            # 保存结果
            print("\n" + "=" * 60)
            print("推荐的选择器 (如果找到)")
            print("=" * 60)

            for category, matches in results.items():
                if matches:
                    print(f"\n{category}:")
                    for m in matches[:3]:
                        print(f"  {m}")

            # 尝试查找所有可见元素
            print("\n" + "=" * 60)
            print("所有可见元素")
            print("=" * 60)

            all_elements = await page.evaluate("""
                () => {
                    const elements = [];
                    const seen = new Set();

                    document.querySelectorAll('input, button, a, span, div').forEach(el => {
                        const key = el.className + el.textContent;
                        if (!seen.has(key) && el.offsetParent !== null) {
                            seen.add(key);
                            const text = (el.textContent || '').trim();
                            if (text.length > 0 && text.length < 100) {
                                elements.push({
                                    tag: el.tagName.toLowerCase(),
                                    class: el.className,
                                    text: text.substring(0, 40)
                                });
                            }
                        }
                    });

                    return elements.slice(0, 30);
                }
            """)

            for el in all_elements:
                print(f"<{el['tag']}> {el['text']}")
                print(f"   class={el['class']}")

            await asyncio.sleep(10)

        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(explore_login_page())
