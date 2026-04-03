"""
Test Patchright (反检测浏览器) for Dewu login
"""
import asyncio
from patchright.async_api import async_playwright

async def main():
    print("=" * 50)
    print("Patchright Anti-Detection Browser Test")
    print("=" * 50)

    async with async_playwright() as pw:
        try:
            print("\nStep 1: Launching browser...")
            # 使用 patchright 的 chromium（反检测版本）
            browser = await pw.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            print("[OK] Browser launched")

            print("\nStep 2: Creating context...")
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
            )
            print("[OK] Context created")

            print("\nStep 3: Creating page...")
            page = await context.new_page()
            print("[OK] Page created")

            print("\nStep 4: Opening Dewu login page...")
            await page.goto('https://creator.dewu.com/login', wait_until='networkidle', timeout=60000)
            print(f"[OK] Page loaded")
            print(f"   Title: {await page.title()}")
            print(f"   URL: {page.url}")

            print("\nStep 5: Saving screenshot...")
            await page.screenshot(path='logs/patchright_dewu.png', full_page=True)
            print("[OK] Screenshot saved: logs/patchright_dewu.png")

            print("\nStep 6: Checking elements...")
            try:
                phone = await page.wait_for_selector('input[placeholder*="phone"]', timeout=5000)
                if phone:
                    print("[OK] Found phone input")
            except:
                print("[INFO] Phone input check skipped")

            input("\nPress Enter to close browser...")

            await browser.close()
            print("\n[OK] Test complete")

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
