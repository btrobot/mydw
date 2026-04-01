---
paths:
  - "backend/**/*.py"
  - "frontend/**/*.ts"
  - "frontend/**/*.tsx"
---

# Security Rules

适用于所有前端和后端代码。

## Sensitive Data Handling

### Storage

- sensitive data MUST be encrypted before storage
- MUST use established encryption libraries (cryptography, AES-256-GCM)
- MUST NOT store sensitive data in plaintext

**Correct** (Python):

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from utils.crypto import encrypt_data, decrypt_data

# Encrypt before storage
encrypted = encrypt_data(cookies)
account = Account(cookies=encrypted)

# Decrypt on demand
plaintext = decrypt_data(account.cookies)
```

**Incorrect**:

```python
# VIOLATION: plaintext storage
account = Account(cookies=cookies)

# VIOLATION: hardcoded encryption key
KEY = "my-secret-key"
```

### Logging

- MUST NOT log sensitive data (passwords, cookies, tokens, API keys)
- MUST use structured logging with appropriate log levels
- errors MUST be logged without exposing sensitive details

**Correct**:

```python
from loguru import logger

logger.info("账号创建成功: account_id={}", account_id)
logger.warning("登录失败: account_name={}, reason=invalid_credentials")

# Log errors without sensitive data
logger.error("处理失败: account_id={}, error_type={}", account_id, type(e).__name__)
```

**Incorrect**:

```python
# VIOLATION: logging sensitive data
logger.info(f"cookies={cookies}")
logger.info(f"password={password}")

# VIOLATION: logging full error with sensitive context
logger.error(f"Failed: {e}, cookies={cookies}")
```

## Input Validation

- all user input MUST be validated
- validation MUST be done server-side (client-side is for UX only)
- file paths MUST be validated to prevent path traversal

**Correct** (Python):

```python
from pydantic import BaseModel, Field, field_validator
from pathlib import Path

class TaskCreate(BaseModel):
    account_id: int = Field(..., gt=0)
    video_path: Optional[str] = Field(None, min_length=1)

    @field_validator('video_path')
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v:
            # Prevent path traversal
            if '..' in v:
                raise ValueError('路径遍历攻击')
            # Ensure relative path
            if v.startswith('/') or ':' in v:
                raise ValueError('必须使用相对路径')
        return v
```

**Incorrect**:

```python
# VIOLATION: trusting user input
def process_file(path: str):
    os.system(f"ffmpeg -i {path}")  # Command injection!

# VIOLATION: missing validation
@router.post("/upload")
async def upload(file: UploadFile):
    content = await file.read()
    # No validation!
```

## SQL Injection Prevention

- queries MUST use ORM (SQLAlchemy) — prevents SQL injection
- MUST NOT use string concatenation for queries

**Correct**:

```python
# Using ORM (safe)
result = await db.execute(
    select(Account).where(Account.account_id == account_id)
)
```

**Incorrect**:

```python
# VIOLATION: SQL injection vulnerability
query = f"SELECT * FROM accounts WHERE id = {account_id}"
await db.execute(text(query))
```

## Authentication (Future)

- API endpoints SHOULD require authentication
- authentication SHOULD use JWT or session tokens
- tokens MUST be validated on each request

**Correct**:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer(auto_error=False)

async def get_current_user(
    token: Optional[str] = Depends(security),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权",
        )

    user = await verify_token(token.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
        )
    return user

@router.delete("/{account_id}")
async def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check ownership
    if not current_user.is_admin and current_user.id != account_id:
        raise HTTPException(status_code=403, detail="无权操作")
    ...
```

## Rate Limiting

- public endpoints SHOULD have rate limits
- rate limits MUST be configurable
- rate limit responses MUST return appropriate headers

**Correct**:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest):
    ...
```

## File Upload Security

- uploaded files MUST be validated for type and size
- file extensions MUST NOT be trusted (check content type)
- uploaded files SHOULD be stored outside web root
- filenames MUST be sanitized

**Correct**:

```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_TYPES = {'video/mp4', 'video/quicktime', 'image/jpeg', 'image/png'}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件过大")

    # Validate MIME type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    # Sanitize filename
    safe_name = Path(file.filename).name.replace('..', '')
    storage_path = Path("data/uploads") / safe_name
    storage_path.write_bytes(content)

    return {"filename": safe_name}
```

**Incorrect**:

```python
# VIOLATION: trusting filename
with open(f"uploads/{file.filename}", "wb") as f:
    f.write(content)

# VIOLATION: no size limit
content = await file.read()  # Could fill disk!
```

## Environment Variables

- secrets MUST be read from environment variables
- MUST NOT have default values for production secrets
- .env files MUST be in .gitignore

**Correct**:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    COOKIE_ENCRYPT_KEY: str  # Required in production

settings = Settings()
```

**Incorrect**:

```python
# VIOLATION: hardcoded secret
COOKIE_ENCRYPT_KEY = "my-secret-key"

# VIOLATION: default secret
COOKIE_ENCRYPT_KEY = "change-this-in-production"
```

## Electron Security

### Main Process

- nodeIntegration MUST be disabled
- contextIsolation MUST be enabled
- sandbox SHOULD be enabled

**Correct**:

```typescript
const mainWindow = new BrowserWindow({
  width: 1280,
  height: 800,
  webPreferences: {
    nodeIntegration: false,
    contextIsolation: true,
    sandbox: true,
    preload: path.join(__dirname, 'preload.js'),
  },
})
```

**Incorrect**:

```typescript
// VIOLATION: insecure configuration
const mainWindow = new BrowserWindow({
  webPreferences: {
    nodeIntegration: true,  // DANGEROUS!
    contextIsolation: false,
  },
})
```

### Preload Script

- MUST expose minimal API via contextBridge
- MUST NOT expose Node.js APIs directly
- MUST validate IPC messages

**Correct**:

```typescript
import { contextBridge, ipcRenderer } from 'electron'

// Expose minimal, safe API
contextBridge.exposeInMainWorld('electronAPI', {
  startBackend: () => ipcRenderer.invoke('start-backend'),
  stopBackend: () => ipcRenderer.invoke('stop-backend'),
  getStatus: () => ipcRenderer.invoke('get-status'),
})
```

**Incorrect**:

```typescript
// VIOLATION: exposing dangerous APIs
contextBridge.exposeInMainWorld('electronAPI', {
  fs: require('fs'),  // DANGEROUS!
  exec: require('child_process').exec,  // DANGEROUS!
  shell: require('electron').shell,
})
```

## Prohibited Patterns

### Python
- MUST NOT use `eval()` or `exec()`
- MUST NOT store secrets in code
- MUST NOT log sensitive data
- MUST NOT skip input validation
- MUST NOT use string concatenation for SQL

### TypeScript
- MUST NOT use `eval()` or `new Function()`
- MUST NOT use `innerHTML` — use `textContent`
- MUST NOT expose Node.js APIs to renderer

### Electron
- MUST NOT enable `nodeIntegration`
- MUST NOT disable `contextIsolation`
- MUST NOT expose `fs` or `child_process` to renderer

## Rationale

These rules prevent:
- Data breaches through sensitive data exposure
- Injection attacks (SQL, command, XSS)
- Authentication bypass
- Denial of service through resource exhaustion
- Remote code execution through unsafe Electron config

## Related Rules

- `python-coding-rules.md` — Python implementation guidelines
- `typescript-coding-rules.md` — TypeScript implementation guidelines
- `electron-rules.md` — Electron-specific security rules
- `api-design-rules.md` — API security requirements
