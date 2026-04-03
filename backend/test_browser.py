"""
最简单的浏览器测试脚本
功能：打开得物创作者登录页并截图
"""
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        # 启动浏览器（用非 headless 模式可以看到）
        browser = await p.chromium.launch(headless=False)

        # 创建页面
        page = await browser.new_page()

        # 打开登录页
        await page.goto("https://creator.dewu.com/login")

        # 等待一下让页面加载
        await page.wait_for_timeout(5000)

        # 截图
        await page.screenshot(path="logs/test_login.png")
        print(f"截图已保存: logs/test_login.png")
        print(f"当前URL: {page.url}")

        # 打印页面标题
        print(f"页面标题: {await page.title()}")

        # 保持浏览器打开，让用户查看
        input("按回车键关闭浏览器...")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
