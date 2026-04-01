---
paths:
  - "backend/**/*.py"
  - "frontend/**/*.ts"
---

# Security Rules - 安全规范

适用于所有代码。

## 敏感数据处理

### 禁止的模式

```typescript
// ❌ 错误：前端暴露敏感数据
const response = await api.get('/account');
return {
  id: response.data.id,
  cookies: response.data.cookies,  // Cookie 不应返回给前端！
};
```

```python
# ❌ 错误：明文存储
class Account:
    cookies = Column(Text)  # 明文存储！
```

### 正确的模式

```typescript
// ✅ 正确：后端不返回 Cookie
interface AccountResponse {
  id: number;
  name: string;
  status: string;
  // 省略 cookies 字段
}
```

```python
# ✅ 正确：加密存储
from utils.crypto import encrypt_data, decrypt_data

class Account(Base):
    _encrypted_cookies = Column(Text)  # 内部字段名

    @property
    def cookies(self):
        return decrypt_data(self._encrypted_cookies)
```

## 输入验证

```python
# ✅ 正确：完整的 Pydantic 验证
from pydantic import BaseModel, Field, validator

class CreateTaskRequest(BaseModel):
    account_id: int = Field(..., gt=0)
    video_path: str = Field(..., min_length=1)

    @validator("video_path")
    def validate_video_path(cls, v: str) -> str:
        if ".." in v:
            raise ValueError("无效的路径")
        return v
```

## 日志脱敏

```python
# ✅ 正确：脱敏日志
logger.info(f"登录成功: account_id={account_id}")

# ❌ 错误：日志泄露
logger.info(f"登录成功: cookies={cookies}")  # 禁止！
```

## 禁止的模式

- ❌ 硬编码密码/API Key
- ❌ 明文存储敏感数据
- ❌ 日志中记录敏感信息
- ❌ 跳过输入验证
- ❌ 返回敏感数据给前端
