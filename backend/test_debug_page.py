"""
调试 Patchright 页面结构
"""
import asyncio
from patchright.async_api import async_playwright

async def main():
    print("=" * 50)
    print("Page Structure Debug")
    print("=" * 50)

    async with async_playwright() as pw:
        try:
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
            )
            page = await context.new_page()

            print("\n[1] Opening login page...")
            await page.goto('https://creator.dewu.com/login', wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(3000)
            await page.screenshot(path='logs/debug_login.png')

            print("\n[2] Page info:")
            print(f"    URL: {page.url}")
            print(f"    Title: {await page.title()}")

            print("\n[3] All buttons:")
            buttons = await page.query_selector_all('button')
            for i, btn in enumerate(buttons):
                text = await btn.text_content()
                disabled = await btn.get_attribute('disabled')
                print(f"    [{i}] text='{text.strip()[:50]}' disabled={disabled}")

            print("\n[4] All inputs:")
            inputs = await page.query_selector_all('input')
            for i, inp in enumerate(inputs):
                inp_type = await inp.get_attribute('type')
                placeholder = await inp.get_attribute('placeholder')
                disabled = await inp.get_attribute('disabled')
                checked = await inp.get_attribute('checked')
                print(f"    [{i}] type={inp_type} placeholder='{placeholder}' disabled={disabled} checked={checked}")

            print("\n[5] All checkboxes:")
            checkboxes = await page.query_selector_all('input[type="checkbox"], input[type="check"]')
            for i, cb in enumerate(checkboxes):
                checked = await cb.is_checked()
                print(f"    [{i}] checked={checked}")

            print("\n[6] Elements containing '获取':")
            elements = await page.query_selector_all('*')
            for el in elements:
                text = await el.text_content()
                if '获取' in text or '验证码' in text:
                    tag = await el.evaluate('el => el.tagName')
                    print(f"    <{tag}> {text.strip()[:60]}")

            print("\n[7] Save full page HTML...")
            content = await page.content()
            with open('logs/debug_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("[OK] Saved to logs/debug_page.html")

            input("\nPress Enter to close...")
            await browser.close()

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
