---
paths:
  - "backend/**/*.py"
---

# Python Coding Rules

适用于 `backend/` 目录下的所有 Python 代码。

## Import Organization

- imports MUST follow this order: stdlib → third-party → local
- imports MUST be grouped with blank lines between groups
- relative imports MUST use explicit relative paths

**Correct**:

```python
# 1. Standard library
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from functools import lru_cache

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field, ConfigDict

# 3. Local application
from models import Account, Task
from schemas.account import AccountResponse
from services.account_service import AccountService
from utils.crypto import encrypt_data, decrypt_data
```

**Incorrect**:

```python
# VIOLATION: wrong order
from fastapi import APIRouter
import os
from models import Account
```

## Type Annotations

- public functions MUST have type annotations for all parameters and return values
- private functions SHOULD have type annotations
- type aliases MUST be defined for complex types

**Correct**:

```python
async def get_account(db: AsyncSession, account_id: int) -> Optional[Account]:
    ...

def validate_path(path: str) -> bool:
    ...

# Type aliases for complex types
AccountDict = Dict[str, Any]
AccountList = List[AccountDict]
```

**Incorrect**:

```python
# VIOLATION: missing type annotations
def get_account(db, account_id):
    ...
```

## Async/Await

- I/O operations MUST use async/await
- async functions MUST NOT call synchronous blocking code
- use httpx for HTTP requests (not requests library)

**Correct**:

```python
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

**Incorrect**:

```python
# VIOLATION: blocking synchronous call in async function
async def fetch_data(url: str) -> dict:
    response = requests.get(url)  # BLOCKING!
    return response.json()
```

## Pydantic Models

- models MUST use Pydantic v2 syntax (model_config, not inner Config class)
- validators MUST use @field_validator decorator
- response models MUST have ConfigDict(from_attributes=True)

**Correct**:

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class AccountResponse(BaseModel):
    """账号响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_name: str
    status: str
    created_at: datetime

class TaskCreate(BaseModel):
    account_id: int = Field(..., gt=0)
    video_path: Optional[str] = Field(None, min_length=1)

    @field_validator('video_path')
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v and '..' in v:
            raise ValueError('路径不能包含 ..')
        return v
```

**Incorrect**:

```python
# VIOLATION: using Pydantic v1 syntax
class AccountResponse(BaseModel):
    class Config:
        from_attributes = True

# VIOLATION: missing Field validation
class TaskCreate(BaseModel):
    account_id: int  # Should use Field
```

## Logging

- MUST use loguru.logger (not print)
- MUST use {} placeholders for structured logging
- MUST NOT log sensitive data (passwords, cookies, API keys)

**Correct**:

```python
from loguru import logger

logger.info("账号创建成功: account_id={}", account_id)
logger.warning("登录失败: account_name={}, reason={}", username, reason)
logger.error("处理失败: error={}", str(e), exc_info=True)
```

**Incorrect**:

```python
# VIOLATION: using print
print("账号创建成功")

# VIOLATION: logging sensitive data
logger.info(f"cookies={cookies}")

# VIOLATION: f-string instead of placeholder
logger.info(f"account_id={account_id}")
```

## Error Handling

- MUST NOT silently catch exceptions (except: pass)
- MUST handle specific exceptions before generic ones
- MUST log errors with context before raising

**Correct**:

```python
try:
    result = await service.get(id)
except ValueError as e:
    logger.warning("无效的 ID: id={}", id)
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error("未知错误: id={}, error={}", id, str(e), exc_info=True)
    raise HTTPException(status_code=500, detail="服务器错误")
```

**Incorrect**:

```python
# VIOLATION: silent exception handling
try:
    result = await service.get(id)
except Exception:
    pass  # Silent failure!
```

## FastAPI Routes

- routers MUST define prefix and tags
- routes SHOULD have docstring descriptions
- routes MUST return appropriate HTTP status codes

**Correct**:

```python
router = APIRouter(prefix="/accounts", tags=["账号管理"])


@router.get("", response_model=List[AccountResponse])
async def list_accounts(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> List[AccountResponse]:
    """获取账号列表（支持分页和状态过滤）"""
    query = select(Account)
    if status:
        query = query.where(Account.status == status)
    return (await db.execute(query.offset(skip).limit(limit))).scalars().all()
```

## SQLAlchemy Queries

- MUST use select() for queries (not text())
- SHOULD use scalars().first() instead of scalar_one_or_none()
- MUST use parameterized queries (ORM prevents SQL injection)

**Correct**:

```python
result = await db.execute(select(Account).where(Account.id == account_id))
account = result.scalars().first()

# Pagination
result = await db.execute(
    select(Account).offset(skip).limit(limit).order_by(Account.created_at.desc())
)
```

**Incorrect**:

```python
# VIOLATION: using raw SQL
result = await db.execute(text(f"SELECT * FROM accounts WHERE id = {account_id}"))
```

## Data Encryption

- sensitive data (cookies, passwords) MUST be encrypted before storage
- MUST use utils.crypto module for encryption/decryption
- MUST NOT log decrypted sensitive data

**Correct**:

```python
from utils.crypto import encrypt_data, decrypt_data

# Encrypt before storage
encrypted = encrypt_data(cookies)
account = Account(cookies=encrypted)

# Decrypt on demand
plaintext = decrypt_data(account.cookies)
```

**Incorrect**:

```python
# VIOLATION: storing plaintext
account = Account(cookies=cookies)

# VIOLATION: logging sensitive data
logger.info(f"cookies={cookies}")
```

## Service Layer

- business logic SHOULD be encapsulated in service classes
- routers SHOULD delegate to services (thin routes, fat services)
- services MUST receive db session as constructor parameter

**Correct**:

```python
class AccountService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        result = await self.db.execute(
            select(Account).where(Account.id == account_id)
        )
        return result.scalars().first()


@router.get("/{account_id}")
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
) -> AccountResponse:
    service = AccountService(db)
    account = await service.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return account
```

## Prohibited Patterns

- MUST NOT use print() — use logger
- MUST NOT use blocking synchronous I/O in async functions
- MUST NOT use Pydantic v1 syntax (inner Config class)
- MUST NOT use `except Exception: pass`
- MUST NOT hardcode secrets/keys
- MUST NOT store sensitive data in plaintext
- MUST NOT log sensitive data (cookies, passwords, API keys)
- MUST NOT use raw SQL — use ORM

## Rationale

These rules ensure:
- Consistent code style across the codebase
- Type safety through explicit annotations
- Non-blocking I/O for high performance
- Security through encryption and input validation
- Maintainability through service layer separation

## Related Rules

- `security-rules.md` — Security requirements for sensitive data handling
- `api-design-rules.md` — API design patterns
- `code-review-rules.md` — Code review checklist
