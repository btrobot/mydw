# Python Style - Python 代码风格

适用于 `backend/` 目录。

## 基本原则

1. **PEP 8**: 遵循 PEP 8 规范
2. **类型注解**: 所有公共函数添加类型注解
3. **异步优先**: I/O 操作使用 async/await
4. **单一职责**: 每个函数/类职责单一

## 导入顺序

```python
# 1. 标准库
import os
import sys
from typing import Optional, List, Dict

# 2. 第三方库
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# 3. 本地导入
from models import Account
from schemas.account import AccountResponse
from utils.crypto import encrypt_data
```

## 类型注解

### 函数注解

```python
# ✅ 正确：完整的类型注解
async def get_account(account_id: int) -> Optional[Account]:
    ...

def validate_path(path: str) -> bool:
    ...

# ❌ 错误：缺少注解
def get_account(account_id):
    ...
```

### 类型别名

```python
# ✅ 正确：类型别名
AccountDict = Dict[str, str]
AccountList = List[AccountDict]
```

## 异步编程

```python
# ✅ 正确：异步函数
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# ✅ 正确：异步上下文管理器
async def get_db():
    async with async_session() as session:
        yield session

# ❌ 错误：混用同步异步
async def wrong():
    result = requests.get("url")  # 同步！
    return result.json()
```

## 日志

```python
# ✅ 正确：Loguru
from loguru import logger

logger.info("用户创建成功: user_id={}", user_id)
logger.warning("登录失败: user={}", username)  # 不记录密码
logger.error("处理失败: {}", error, exc_info=True)

# ❌ 错误：print
print("用户创建成功")  # 无法追踪
```

## 异常处理

```python
# ✅ 正确：具体异常
try:
    result = await service.get(id)
except ValueError as e:
    logger.warning(f"无效的 ID: {id}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"未知错误: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="服务器错误")
```

## 数据加密

```python
# ✅ 正确：加密存储敏感数据
from utils.crypto import encrypt_data, decrypt_data

class AccountService:
    async def create(self, db: AsyncSession, cookies: str) -> Account:
        # 加密存储
        encrypted = encrypt_data(cookies)
        account = Account(cookies=encrypted)
        ...

# ❌ 错误：明文存储
class AccountService:
    async def create(self, db: AsyncSession, cookies: str) -> Account:
        account = Account(cookies=cookies)  # 明文！
        ...
```

## 禁止的模式

- ❌ `print`（使用 logger）
- ❌ 同步 I/O（在 async 函数中）
- ❌ 缺少类型注解的公共函数
- ❌ `except Exception`
- ❌ 硬编码密钥
- ❌ 明文存储敏感数据
- ❌ 日志中记录敏感信息
