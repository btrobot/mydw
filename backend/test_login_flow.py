"""
测试得物登录流程 - 验证页面元素交互
功能：输入手机号、点击获取验证码
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from loguru import logger

# 确保logs目录存在
Path("logs").mkdir(exist_ok=True)

# 得物登录页元素选择器
SELECTORS = {
    "phone_input": [
        'input[type="tel"]',
        'input[placeholder*="手机"]',
        'input[placeholder*="phone"]',
    ],
    "agree_checkbox": [
        'input[type="checkbox"]',
        '[class*="agree"]',
        '[class*="protocol"]',
        '[class*="privacy"]',
        '.ant-checkbox-input',
    ],
    "code_button": [
        'button:has-text("获取验证码")',
        'button:has-text("发送")',
        'button:has-text("验证码")',
    ],
    "code_input": [
        'input[maxlength="6"]',
        'input[placeholder*="验证码"]',
        'input[placeholder*="码"]',
    ],
    "login_button": [
        'button:has-text("登录")',
        'button:has-text("下一步")',
    ],
}


async def find_element(page, selectors_list: list[str], timeout: int = 5000):
    """尝试多个选择器，返回第一个找到的元素"""
    for selector in selectors_list:
        try:
            element = await page.wait_for_selector(selector, timeout=timeout)
            if element:
                return element, selector
        except PlaywrightTimeout:
            continue
    return None, None


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 50)
        print("步骤 1: 打开登录页")
        print("=" * 50)
        await page.goto("https://creator.dewu.com/login")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="logs/step1_login_page.png")
        print(f"页面标题: {await page.title()}")
        print(f"URL: {page.url}")

        print("\n" + "=" * 50)
        print("步骤 2: 查找并点击手机号输入框")
        print("=" * 50)
        phone_input, phone_selector = await find_element(page, SELECTORS["phone_input"])
        if phone_input:
            print(f"[OK] 找到手机号输入框: {phone_selector}")
            await page.screenshot(path="logs/step2_phone_found.png")

            print("\n" + "=" * 50)
            print("步骤 2.5: 查找并勾选同意协议复选框")
            print("=" * 50)
            checkbox, checkbox_selector = await find_element(page, SELECTORS["agree_checkbox"])
            if checkbox:
                print(f"[OK] 找到协议复选框: {checkbox_selector}")
                await checkbox.check()
                await page.wait_for_timeout(500)
                await page.screenshot(path="logs/step25_checkbox.png")
            else:
                print("[WARN] 未找到协议复选框（可能已默认勾选）")

            print("\n" + "=" * 50)
            print("步骤 3: 输入手机号")
            print("=" * 50)
            # 使用测试手机号（可以是不存在的，看验证码发送逻辑）
            test_phone = "13800138000"
            await phone_input.fill(test_phone)
            print(f"[OK] 已输入手机号: {test_phone}")
            await page.wait_for_timeout(500)
            await page.screenshot(path="logs/step3_phone_filled.png")
        else:
            print("[FAIL] 未找到手机号输入框")
            await page.screenshot(path="logs/step2_phone_not_found.png")
            # 打印页面上的所有 input 元素
            inputs = await page.query_selector_all("input")
            print(f"页面上的 input 元素数量: {len(inputs)}")
            for i, inp in enumerate(inputs[:5]):
                print(f"  [{i}] {await inp.get_attribute('outerHTML')[:100]}")

        print("\n" + "=" * 50)
        print("步骤 4: 查找验证码按钮")
        print("=" * 50)
        code_button, btn_selector = await find_element(page, SELECTORS["code_button"])
        if code_button:
            print(f"[OK] 找到验证码按钮: {btn_selector}")
            await page.screenshot(path="logs/step4_code_button.png")

            print("\n" + "=" * 50)
            print("步骤 5: 点击获取验证码")
            print("=" * 50)
            await code_button.click()
            print("[OK] 已点击验证码按钮")
            await page.wait_for_timeout(2000)
            await page.screenshot(path="logs/step5_after_click.png")

            # 检查验证码输入框是否出现
            code_input, code_selector = await find_element(page, SELECTORS["code_input"])
            if code_input:
                print(f"[OK] 验证码输入框出现: {code_selector}")
            else:
                print("[WARN] 验证码输入框未出现（可能需要先登录或页面逻辑不同）")
        else:
            print("[FAIL] 未找到验证码按钮")
            buttons = await page.query_selector_all("button")
            print(f"页面上的 button 元素数量: {len(buttons)}")
            for i, btn in enumerate(buttons[:10]):
                text = await btn.text_content()
                print(f"  [{i}] {text.strip()[:50]}")

        print("\n" + "=" * 50)
        print("测试完成，查看截图分析页面结构")
        print("=" * 50)
        print("\n截图文件:")
        print("  - logs/step1_login_page.png")
        print("  - logs/step2_phone_found.png 或 step2_phone_not_found.png")
        print("  - logs/step25_checkbox.png")
        print("  - logs/step3_phone_filled.png")
        print("  - logs/step4_code_button.png")
        print("  - logs/step5_after_click.png")

        input("\n按回车键关闭浏览器...")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
