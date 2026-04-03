"""
测试得物手机验证码登录 - 完整交互流程
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# 确保logs目录存在
Path("logs").mkdir(exist_ok=True)

# 选择器配置
SELECTORS = {
    "phone_input": ['input[placeholder*="手机"]'],
    "agree_checkbox": ['input[type="checkbox"]'],
    "code_button": ['button:has-text("获取")'],
    "code_input": ['input[placeholder*="验证码"]'],
    "login_button": ['button:has-text("登录")'],
}


async def find_element(page, selectors_list, timeout=5000):
    """尝试多个选择器，返回第一个匹配的元素"""
    for selector in selectors_list:
        try:
            element = await page.wait_for_selector(selector, timeout=timeout)
            if element:
                return element, selector
        except PlaywrightTimeout:
            continue
    return None, None


async def main():
    """主测试流程"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 1. 打开登录页
        print("=" * 50)
        print("步骤 1: 打开登录页")
        print("=" * 50)
        await page.goto("https://creator.dewu.com/login")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="logs/sms_step1.png")
        print(f"页面标题: {await page.title()}")
        print(f"当前URL: {page.url}")

        # 2. 勾选协议复选框
        print("\n" + "=" * 50)
        print("步骤 2: 勾选协议复选框")
        print("=" * 50)
        checkbox, used_selector = await find_element(page, SELECTORS["agree_checkbox"])
        if checkbox:
            is_checked = await checkbox.is_checked()
            if not is_checked:
                await checkbox.check()
            print(f"协议复选框已勾选 (选择器: {used_selector})")
        else:
            print("未找到协议复选框")
            await page.screenshot(path="logs/sms_step2_failed.png")
        await page.wait_for_timeout(300)

        # 3. 输入手机号
        print("\n" + "=" * 50)
        print("步骤 3: 输入手机号")
        print("=" * 50)
        phone_input, used_selector = await find_element(page, SELECTORS["phone_input"])
        if phone_input:
            test_phone = input("\n请输入测试手机号: ").strip()
            if test_phone:
                await phone_input.fill(test_phone)
                print(f"已输入手机号: {test_phone}")
            else:
                print("未输入手机号，跳过后续步骤")
                await browser.close()
                return
        else:
            print("未找到手机号输入框")
            await browser.close()
            return
        await page.wait_for_timeout(500)
        await page.screenshot(path="logs/sms_step3.png")

        # 4. 点击获取验证码
        print("\n" + "=" * 50)
        print("步骤 4: 点击获取验证码")
        print("=" * 50)
        code_button, used_selector = await find_element(page, SELECTORS["code_button"])
        if code_button:
            await code_button.click()
            print(f"已点击验证码按钮 (选择器: {used_selector})")
        else:
            print("未找到验证码按钮")
            await page.screenshot(path="logs/sms_step4_failed.png")
            await browser.close()
            return
        await page.wait_for_timeout(2000)
        await page.screenshot(path="logs/sms_step4.png")

        # 5. 检查验证码输入框是否出现
        print("\n" + "=" * 50)
        print("步骤 5: 检查验证码输入框")
        print("=" * 50)
        code_input, used_selector = await find_element(page, SELECTORS["code_input"])
        if code_input:
            print(f"验证码输入框已出现 (选择器: {used_selector})")
            await page.screenshot(path="logs/sms_step5.png")

            # 6. 输入验证码
            print("\n" + "=" * 50)
            print("步骤 6: 输入验证码")
            print("=" * 50)
            code = input("\n请输入收到的验证码: ").strip()
            if code:
                await code_input.fill(code)
                print(f"已输入验证码")
            else:
                print("未输入验证码，跳过登录")
                await browser.close()
                return
            await page.wait_for_timeout(500)
            await page.screenshot(path="logs/sms_step6.png")

            # 7. 点击登录按钮
            print("\n" + "=" * 50)
            print("步骤 7: 点击登录按钮")
            print("=" * 50)
            login_button, used_selector = await find_element(page, SELECTORS["login_button"])
            if login_button:
                await login_button.click()
                print(f"已点击登录按钮 (选择器: {used_selector})")
            else:
                print("未找到登录按钮")
                await page.screenshot(path="logs/sms_step7_failed.png")
                await browser.close()
                return
            await page.wait_for_timeout(3000)
            await page.screenshot(path="logs/sms_step7.png")

            # 8. 检查登录结果
            print("\n" + "=" * 50)
            print("步骤 8: 检查登录结果")
            print("=" * 50)
            current_url = page.url
            print(f"当前URL: {current_url}")

            if "login" not in current_url.lower():
                print("登录成功！已跳转到其他页面")
            else:
                print("可能未登录成功，仍在登录页")
                await page.screenshot(path="logs/sms_step8_error.png")
        else:
            print("验证码输入框未出现")
            await page.screenshot(path="logs/sms_step5_failed.png")

        print("\n" + "=" * 50)
        print("测试完成")
        print("=" * 50)
        input("\n按回车键关闭浏览器...")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
