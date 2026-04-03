"""
测试 Patchright 登录流程（详细调试版）
"""
import asyncio
from patchright.async_api import async_playwright

async def main():
    print("=" * 50)
    print("Patchright Login Debug Test")
    print("=" * 50)

    async with async_playwright() as pw:
        try:
            # 1. 启动浏览器
            print("\n[1] Launching browser...")
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                locale='zh-CN',
            )
            page = await context.new_page()
            print("[OK] Browser launched")

            # 2. 打开登录页
            print("\n[2] Opening login page...")
            await page.goto('https://creator.dewu.com/login', wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path='logs/debug2_1.png')
            print(f"[OK] Page loaded")

            # 3. 勾选协议
            print("\n[3] Checking checkbox...")
            checkbox = await page.query_selector('input[type="checkbox"]')
            if checkbox:
                await checkbox.check()
                print("[OK] Checkbox checked")
            await page.wait_for_timeout(500)

            # 4. 输入手机号
            print("\n[4] Entering phone...")
            phone = input("Phone: ").strip()
            if not phone:
                await browser.close()
                return

            phone_input = await page.query_selector('input[placeholder*="手机"]')
            await phone_input.fill(phone)
            print(f"[OK] Phone entered: {phone[:3]}****")
            await page.wait_for_timeout(500)
            await page.screenshot(path='logs/debug2_2.png')

            # 5. 点击发送验证码
            print("\n[5] Clicking send code...")
            buttons = await page.query_selector_all('button')
            for btn in buttons:
                text = await btn.text_content()
                if '验证码' in text or '发送' in text:
                    await btn.click()
                    print(f"[OK] Clicked: '{text.strip()}'")
                    break
            await page.wait_for_timeout(3000)
            await page.screenshot(path='logs/debug2_3.png')

            # 6. 打印页面所有输入框状态
            print("\n[6] Input fields status:")
            inputs = await page.query_selector_all('input')
            for inp in inputs:
                placeholder = await inp.get_attribute('placeholder')
                inp_type = await inp.get_attribute('type')
                value = await inp.input_value()
                disabled = await inp.get_attribute('disabled')
                print(f"    type={inp_type}, placeholder='{placeholder}', value='{value[:20] if value else ''}', disabled={disabled}")

            # 7. 检查是否有错误提示
            print("\n[7] Checking for error messages...")
            error_selectors = ['.ant-form-item-explain-error', '[class*="error"]', '.ant-message']
            for selector in error_selectors:
                errors = await page.query_selector_all(selector)
                for err in errors:
                    text = await err.text_content()
                    if text.strip():
                        print(f"    ERROR [{selector}]: {text.strip()}")

            # 8. 输入验证码
            print("\n[8] Entering code...")
            code = input("Code: ").strip()
            if not code:
                await browser.close()
                return

            # 尝试找到验证码输入框
            code_input = await page.query_selector('input[placeholder*="验证码"]')
            if code_input:
                # 先点击输入框确保获得焦点
                await code_input.click()
                await page.wait_for_timeout(200)
                # 逐字输入验证码（某些网站需要这样）
                await code_input.fill(code)
                print(f"[OK] Code entered: {code[:2]}**")
            else:
                print("[WARN] Code input not found, trying all inputs")
                inputs = await page.query_selector_all('input')
                for inp in inputs:
                    placeholder = await inp.get_attribute('placeholder')
                    if '验证码' in str(placeholder):
                        await inp.click()
                        await page.wait_for_timeout(200)
                        await inp.fill(code)
                        print(f"[OK] Code entered via fallback")
                        break
            await page.wait_for_timeout(1000)
            await page.screenshot(path='logs/debug2_4.png')

            # 打印验证码输入框的值
            code_input_check = await page.query_selector('input[placeholder*="验证码"]')
            if code_input_check:
                val = await code_input_check.input_value()
                print(f"    Code input value: '{val}'")

            # 9. 再次检查错误
            print("\n[9] Error check after code:")
            for selector in error_selectors:
                errors = await page.query_selector_all(selector)
                for err in errors:
                    text = await err.text_content()
                    if text.strip():
                        print(f"    ERROR: {text.strip()}")

            # 10. 点击登录
            print("\n[10] Clicking login...")
            # 使用精确选择器，避免误点"密码登录"按钮
            # "登录" 按钮的文本是 "登 录"（中间有空格）
            # "密码登录" 不应该被匹配
            login_button = await page.query_selector('button:has-text("登 录")')
            if not login_button:
                # 备用：精确匹配 "登录" 或 "登 录"
                all_buttons = await page.query_selector_all('button')
                for btn in all_buttons:
                    text = await btn.text_content()
                    text_clean = text.strip()
                    # 只匹配单独的"登录"或"登 录"，不匹配"密码登录"
                    if text_clean in ['登录', '登 录'] and '密码' not in text_clean:
                        login_button = btn
                        print(f"[OK] Found login button: '{text_clean}'")
                        break

            if not login_button:
                print("[WARN] Login button not found, listing all buttons:")
                buttons = await page.query_selector_all('button')
                for i, btn in enumerate(buttons):
                    text = await btn.text_content()
                    print(f"    [{i}] '{text.strip()}'")
            else:
                print("[OK] Clicking login button")
                await login_button.click()
                print("[OK] Login clicked")
            await page.wait_for_timeout(5000)  # 等待更长时间
            await page.screenshot(path='logs/debug2_5.png')

            # 11. 最终URL检查
            print("\n[11] Final check:")
            url = page.url
            print(f"    URL: {url}")

            # 检测登录成功：URL 不包含 login 且不等于原 URL
            login_url = 'https://creator.dewu.com/login'
            if "login" not in url.lower() and url != login_url:
                print("[SUCCESS] Login successful! Redirected to:", url)
                await page.wait_for_load_state('networkidle')
                await page.screenshot(path='logs/debug2_result_success.png')
            else:
                print("[INFO] Still on login page")
                await page.screenshot(path='logs/debug2_result_login.png')

            input("\nPress Enter to close...")
            await browser.close()

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
