"""
手动登录并导出 Session（自动检测版）
"""
import asyncio
import json
import time
from patchright.async_api import async_playwright

async def main():
    print("=" * 50)
    print("Manual Login & Export Session (Auto)")
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
            print("[OK] Login page opened")

            # 3. 等待用户手动登录（最多等待 5 分钟）
            print("\n[3] Waiting for manual login...")
            print("    Please login in the browser window.")
            print("    The script will auto-detect when you reach the upload page.")
            print("    Or press Enter to check now...")

            # 监控 URL 变化
            login_url = page.url
            max_wait = 300  # 5 分钟
            start_time = time.time()

            while time.time() - start_time < max_wait:
                current_url = page.url

                # 检测是否跳转到非登录页面
                if "login" not in current_url.lower() and current_url != login_url:
                    print(f"\n[SUCCESS] Login detected!")
                    print(f"    New URL: {current_url}")

                    # 等待页面完全加载
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(2000)

                    # 截图确认
                    await page.screenshot(path='logs/logged_in.png')
                    print("[OK] Screenshot saved: logs/logged_in.png")

                    # 导出 session
                    print("\n[4] Exporting session...")
                    state = await context.storage_state()

                    with open('logs/dewu_session.json', 'w', encoding='utf-8') as f:
                        json.dump(state, f, indent=2, ensure_ascii=False)
                    print("[OK] Session saved: logs/dewu_session.json")

                    # 打印 session 信息
                    print("\n[5] Session info:")
                    cookies = state.get('cookies', [])
                    print(f"    Cookies: {len(cookies)} items")
                    for cookie in cookies[:3]:
                        name = cookie['name']
                        value = cookie['value'][:30] + "..." if len(cookie['value']) > 30 else cookie['value']
                        print(f"      - {name}: {value}")

                    input("\nPress Enter to close browser...")
                    await browser.close()
                    print("[OK] Done!")
                    return

                await asyncio.sleep(1)

            print("\n[WARN] Timeout waiting for login")
            await page.screenshot(path='logs/login_timeout.png')

            input("\nPress Enter to close browser...")
            await browser.close()

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
