"""
测试得物登录 API

用法:
    python -m scripts.test_login_api

注意: 运行前请确保:
    1. 后端服务已启动 (uvicorn main:app --reload)
    2. 账号已创建 (POST /api/accounts/)
    3. 有可用的手机号接收验证码
"""
import asyncio
import httpx
from typing import Optional

BASE_URL = "http://localhost:8000/api"


async def test_login_flow():
    """测试完整的登录流程"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. 创建测试账号（如果不存在则跳过）
        print("\n=== 1. 创建测试账号 ===")
        try:
            response = await client.post(
                f"{BASE_URL}/accounts/",
                json={
                    "account_id": "test_account_001",
                    "account_name": "测试账号"
                }
            )
            if response.status_code in (201, 400):
                print(f"账号准备就绪: {response.json().get('account_name', '已存在')}")
            else:
                print(f"创建账号失败: {response.text}")
        except Exception as e:
            print(f"创建账号异常: {e}")

        # 2. 获取账号列表，找到测试账号的 ID
        print("\n=== 2. 获取账号列表 ===")
        try:
            response = await client.get(f"{BASE_URL}/accounts/")
            accounts = response.json()
            test_account = next(
                (acc for acc in accounts if acc["account_id"] == "test_account_001"),
                None
            )
            if test_account:
                account_id = test_account["id"]
                print(f"找到测试账号: ID={account_id}, name={test_account['account_name']}")
            else:
                print("未找到测试账号，请先创建")
                return
        except Exception as e:
            print(f"获取账号列表失败: {e}")
            return

        # 3. 检查登录状态
        print("\n=== 3. 检查初始登录状态 ===")
        try:
            response = await client.get(f"{BASE_URL}/accounts/login/{account_id}/status")
            status = response.json()
            print(f"登录状态: {status}")
        except Exception as e:
            print(f"检查登录状态失败: {e}")

        # 4. 获取登录页面截图（调试用）
        print("\n=== 4. 获取登录页面截图 ===")
        try:
            response = await client.get(f"{BASE_URL}/accounts/login/{account_id}/screenshot")
            result = response.json()
            if result.get("success"):
                print(f"截图已保存: {result.get('screenshot_path')}")
                print(f"当前 URL: {result.get('url')}")
            else:
                print(f"获取截图失败: {result.get('message')}")
        except Exception as e:
            print(f"获取截图异常: {e}")

        # 5. 执行手机验证码登录（需要真实的手机号和验证码）
        print("\n=== 5. 手机验证码登录 ===")
        print("提示: 请提供真实的手机号和验证码进行测试")
        print("示例:")
        print('   POST /api/accounts/login/{id}')
        print('   Body: {"phone": "13800138000", "code": "123456"}')

        # 这里不实际执行，因为需要真实的验证码
        # phone = input("请输入手机号: ")
        # code = input("请输入验证码: ")

        # 如果有测试验证码，可以在这里执行
        # try:
        #     response = await client.post(
        #         f"{BASE_URL}/accounts/login/{account_id}",
        #         json={"phone": phone, "code": code}
        #     )
        #     result = response.json()
        #     print(f"登录结果: {result}")
        # except Exception as e:
        #     print(f"登录失败: {e}")

        # 6. 导出登录会话
        print("\n=== 6. 导出登录会话 ===")
        try:
            response = await client.post(f"{BASE_URL}/accounts/login/{account_id}/export")
            result = response.json()
            if result.get("success"):
                print("会话导出成功")
                print(f"Storage state 长度: {len(result.get('storage_state', ''))} 字符")
            else:
                print(f"导出失败: {result.get('message')}")
        except Exception as e:
            print(f"导出会话失败: {e}")


async def test_api_endpoints():
    """测试 API 端点可用性"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        endpoints = [
            ("GET", "/accounts/", "获取账号列表"),
            ("GET", "/accounts/stats", "获取账号统计"),
            ("POST", "/accounts/", "创建账号"),
        ]

        print("\n=== API 端点测试 ===")
        for method, path, description in endpoints:
            try:
                url = f"{BASE_URL}{path}"
                if method == "GET":
                    response = await client.get(url)
                else:
                    response = await client.post(url, json={})

                status_icon = "OK" if response.status_code < 400 else "FAIL"
                print(f"[{status_icon}] {method} {path} - {description} ({response.status_code})")
            except httpx.ConnectError:
                print(f"[ERR] {method} {path} - 无法连接到服务器")
            except Exception as e:
                print(f"[ERR] {method} {path} - {e}")


async def main():
    print("=" * 60)
    print("得物登录 API 测试")
    print("=" * 60)

    # 测试 API 可用性
    await test_api_endpoints()

    # 测试登录流程
    await test_login_flow()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
