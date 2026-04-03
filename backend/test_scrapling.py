"""
Test Scrapling DynamicFetcher for Dewu login page (with browser interaction)
"""
import asyncio
from scrapling.fetchers import DynamicFetcher

async def main():
    print("=" * 50)
    print("Scrapling DynamicFetcher Test")
    print("=" * 50)

    try:
        print("\nStep 1: Creating DynamicFetcher...")
        fetcher = DynamicFetcher()
        print("[OK] DynamicFetcher created")

        print("\nStep 2: Opening Dewu login page...")
        print("   URL: https://creator.dewu.com/login")
        page = await fetcher.async_fetch(
            'https://creator.dewu.com/login',
            headless=False,
            network_idle=True,
            timeout=60000
        )
        print("[OK] Page loaded")
        print(f"   Title: {page.page.title()}")
        print(f"   URL: {page.page.url}")

        print("\nStep 3: Saving screenshot...")
        await page.page.screenshot(path="logs/scrapling_dewu.png", full_page=True)
        print("[OK] Screenshot saved: logs/scrapling_dewu.png")

        print("\nStep 4: Checking page elements...")
        try:
            phone_input = await page.page.wait_for_selector('input[placeholder*="phone"]', timeout=5000)
            if phone_input:
                print("[OK] Found phone input")
            else:
                print("[WARN] Phone input not found")
        except Exception as e:
            print(f"Element check: {e}")

        input("\nPress Enter to close browser...")

        await page.close()
        print("\n[OK] Test complete")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
