---
paths:
  - "backend/**/*.py"
  - "frontend/src/**/*.ts"
  - "frontend/src/**/*.tsx"
---

# API Design Rules

适用于后端 API 路由和前端 API 服务定义。

## RESTful Conventions

- endpoints MUST use plural nouns for resources
- endpoints MUST follow consistent URL structure
- HTTP methods MUST match resource operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /accounts | List accounts |
| GET | /accounts/{id} | Get single account |
| POST | /accounts | Create account |
| PUT | /accounts/{id} | Update account |
| DELETE | /accounts/{id} | Delete account |

**Correct**:

```python
router = APIRouter(prefix="/accounts", tags=["账号管理"])

@router.get("", response_model=List[AccountResponse])
async def list_accounts(...): ...

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(...): ...

@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(...): ...
```

**Incorrect**:

```python
# VIOLATION: inconsistent naming
@router.get("/get_account")
async def get_account(...): ...

@router.get("/accounts")
async def list_accounts(...): ...

# VIOLATION: singular nouns
@router.get("/account/{id}")
```

## Request Validation

- all user input MUST be validated with Pydantic schemas
- field validators MUST check for invalid values
- path parameters MUST be validated for existence

**Correct**:

```python
from pydantic import BaseModel, Field, field_validator

class TaskCreate(BaseModel):
    account_id: int = Field(..., gt=0, description="账号ID")
    video_path: Optional[str] = Field(None, min_length=1)

    @field_validator('video_path')
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v and '..' in v:
            raise ValueError('路径不能包含 ..')
        if v and v.startswith('/'):
            raise ValueError('必须使用相对路径')
        return v
```

## Response Models

- responses MUST use typed Pydantic models
- sensitive fields MUST NOT be included in response models
- list responses MUST include pagination metadata

**Correct**:

```python
# Response model excludes sensitive fields
class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_name: str
    status: str
    # Note: cookies field is NOT included

# Paginated list response
class PaginatedResponse(BaseModel):
    total: int
    items: List[AccountResponse]
    skip: int
    limit: int
```

**Incorrect**:

```python
# VIOLATION: exposing sensitive data
class AccountResponse(BaseModel):
    cookies: str  # EXPOSED!

# VIOLATION: no pagination
@router.get("")
async def list_accounts(...):
    return accounts  # No metadata
```

## HTTP Status Codes

- GET success: 200 OK
- POST created: 201 Created
- PUT updated: 200 OK
- DELETE success: 204 No Content
- Not found: 404 Not Found
- Validation error: 400 Bad Request
- Server error: 500 Internal Server Error

**Correct**:

```python
@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(...):
    if existing:
        raise HTTPException(status_code=400, detail="账号已存在")
    return account

@router.get("/{account_id}")
async def get_account(...):
    account = await service.get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return account

@router.delete("/{account_id}", status_code=204)
async def delete_account(...):
    ...
    return None
```

## Error Responses

- errors MUST return consistent structure
- errors MUST include user-friendly messages
- sensitive details MUST NOT be exposed

**Correct**:

```python
# Consistent error format
raise HTTPException(
    status_code=404,
    detail="账号不存在"
)

raise HTTPException(
    status_code=400,
    detail="无效的请求参数"
)
```

**Incorrect**:

```python
# VIOLATION: exposing internal details
raise HTTPException(
    status_code=500,
    detail=f"Database error: {e}"  # Leaking internals!
)

# VIOLATION: inconsistent error format
raise HTTPException(detail="Not found")
raise HTTPException(detail={"error": "Not found"})
```

## TypeScript API Types

- frontend MUST define matching TypeScript interfaces
- API responses MUST be typed
- error responses SHOULD be typed

**Correct**:

```typescript
// frontend/src/types/api.ts

// Response types
interface AccountResponse {
  id: number
  account_name: string
  status: string
}

interface PaginatedResponse<T> {
  total: number
  items: T[]
  skip: number
  limit: number
}

// Error response type
interface ApiError {
  detail: string
}

// Service with typed responses
export const accountService = {
  list: () => api.get<PaginatedResponse<AccountResponse>>('/accounts'),
  get: (id: number) => api.get<AccountResponse>(`/accounts/${id}`),
}
```

## CORS Configuration

- CORS origins MUST be explicitly configured
- production MUST NOT use wildcard origins
- credentials MUST be handled carefully

**Correct**:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Explicit origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**Incorrect**:

```python
# VIOLATION: wildcard in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Insecure!
    ...
)
```

## API Versioning

- APIs SHOULD include version prefix
- breaking changes MUST increment version

**Correct**:

```python
# Version in URL path
router = APIRouter(prefix="/api/v1/accounts")
router = APIRouter(prefix="/api/v2/accounts")
```

## Prohibited Patterns

- MUST NOT expose sensitive data in responses
- MUST NOT return different error formats
- MUST NOT use wildcard CORS origins in production
- MUST NOT log sensitive user data
- MUST NOT skip input validation

## Rationale

These rules ensure:
- Consistent API structure across all endpoints
- Security through proper CORS and input validation
- Type safety through typed contracts
- Maintainability through standard conventions

## Related Rules

- `python-coding-rules.md` — Python backend implementation
- `typescript-coding-rules.md` — TypeScript frontend implementation
- `security-rules.md` — Security requirements
