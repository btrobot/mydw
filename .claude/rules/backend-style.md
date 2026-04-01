---
paths:
  - "backend/**/*.py"
---

# Backend Style Guide

Python and FastAPI coding standards for the 得物掘金工具 backend.

## Rule Statements

- All API endpoints MUST use Pydantic models for request/response validation
- Async functions MUST be used for I/O operations
- Database sessions MUST be properly closed in finally blocks or use context managers
- Sensitive data MUST NOT be logged
- Error responses MUST return appropriate HTTP status codes
- API routes MUST be organized in `backend/api/` module

## Rationale

Pydantic validation ensures data integrity. Async operations improve performance. Proper resource management prevents leaks. Logging restrictions protect user data. Clear HTTP codes improve API usability.

## Examples

**Correct**:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

class AccountCreate(BaseModel):
    name: str
    cookie: str

@router.post("/accounts", response_model=AccountResponse)
async def create_account(data: AccountCreate):
    try:
        account = await account_service.create(data)
        return account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Incorrect**:

```python
@router.post("/accounts")
async def create_account(request: Request):
    # No validation, logging sensitive data
    logger.info(f"Creating account with cookie: {request.cookies}")
    account = await account_service.create(request.json())
    return {"account": account}
```

## Related Rules

- `security.md` — Security best practices
- `typescript-guards.md` — TypeScript type guards
