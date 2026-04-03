"""
测试 Patchright 完整登录流程（修正版）
"""
import asyncio
from patchright.async_api import async_playwright

async def main():
    print("=" * 50)
    print("Patchright Login Flow Test")
    print("=" * 50)

    async with async_playwright() as pw:
        try:
            # 1. 启动浏览器
            print("\n[1] Launching browser...")
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
            )
            page = await context.new_page()
            print("[OK] Browser launched")

            # 2. 打开登录页
            print("\n[2] Opening login page...")
            await page.goto('https://creator.dewu.com/login', wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path='logs/login_1_page.png')
            print(f"[OK] Page: {await page.title()}")

            # 3. 勾选协议
            print("\n[3] Checking agreement checkbox...")
            checkbox = await page.query_selector('input[type="checkbox"]')
            if checkbox:
                is_checked = await checkbox.is_checked()
                if not is_checked:
                    await checkbox.check()
                print("[OK] Checkbox checked")
            await page.wait_for_timeout(500)

            # 4. 输入手机号
            print("\n[4] Entering phone number...")
            phone = input("Enter phone number: ").strip()
            if not phone:
                print("[CANCEL]")
                await browser.close()
                return

            phone_input = await page.query_selector('input[placeholder*="手机"]')
            await phone_input.fill(phone)
            print(f"[OK] Phone: {phone[:3]}****")
            await page.wait_for_timeout(500)
            await page.screenshot(path='logs/login_2_phone.png')

            # 5. 点击发送验证码
            print("\n[5] Clicking send code button...")
            code_button = await page.query_selector('button:has-text("发送验证码")')
            if code_button:
                await code_button.click()
                print("[OK] Clicked: 发送验证码")
            else:
                print("[WARN] Button not found, trying generic selector")
                buttons = await page.query_selector_all('button')
                for btn in buttons:
                    text = await btn.text_content()
                    if '验证码' in text:
                        await btn.click()
                        print(f"[OK] Clicked: {text.strip()}")
                        break
            await page.wait_for_timeout(2000)
            await page.screenshot(path='logs/login_3_code_sent.png')

            # 6. 输入验证码
            print("\n[6] Entering verification code...")
            code = input("Enter verification code: ").strip()
            if not code:
                print("[CANCEL]")
                await browser.close()
                return

            code_input = await page.query_selector('input[placeholder*="验证码"]')
            if code_input:
                await code_input.fill(code)
                print(f"[OK] Code entered")
            await page.wait_for_timeout(500)

            # 7. 点击登录
            print("\n[7] Clicking login button...")
            login_button = await page.query_selector('button:has-text("登录")')
            if login_button:
                await login_button.click()
                print("[OK] Clicked: 登录")
            else:
                print("[WARN] Trying alternate selector")
                login_button = await page.query_selector('button:has-text("登 录")')
                if login_button:
                    await login_button.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path='logs/login_4_result.png')

            # 8. 检查结果
            print("\n[8] Checking result...")
            url = page.url
            print(f"Current URL: {url}")
            if "login" not in url.lower():
                print("[SUCCESS] Login successful!")
            else:
                print("[INFO] Still on login page")

            input("\nPress Enter to close...")
            await browser.close()
            print("[OK] Done")

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
