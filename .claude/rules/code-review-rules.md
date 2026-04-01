---
paths:
  - "backend/**/*.py"
  - "frontend/**/*.ts"
  - "frontend/**/*.tsx"
---

# Code Review Rules

适用于所有需要审查的代码。

## Review Process

- code MUST be reviewed before merging
- reviewers MUST check against these rules
- all feedback MUST be addressed or documented

## Mandatory Checks

### Type Safety

- [ ] No `any` types in TypeScript code
- [ ] No `as any` type assertions
- [ ] All Python functions have type annotations
- [ ] Pydantic models use `ConfigDict` not inner `Config`

### Error Handling

- [ ] All async operations have try-catch
- [ ] Errors are logged appropriately
- [ ] Sensitive data is not logged
- [ ] User-friendly error messages are returned

### Security

- [ ] No hardcoded secrets or API keys
- [ ] No sensitive data in responses
- [ ] Input validation present
- [ ] SQL queries use ORM
- [ ] Electron uses secure configuration

### Code Quality

- [ ] Functions are small and focused (< 50 lines)
- [ ] No code duplication
- [ ] Proper naming conventions
- [ ] Comments explain "why" not "what"

## Severity Levels

### Blocking (MUST fix before merge)

- Security vulnerabilities
- `any` type usage
- Missing authentication/authorization
- Exposing sensitive data
- Hardcoded secrets
- Silent exception handling

### Warning (SHOULD fix)

- Code duplication
- Functions too long
- Missing error handling for edge cases
- Inconsistent naming
- Missing type annotations (Python)

### Suggestion (MAY fix)

- Code style preferences
- Minor optimizations
- Documentation improvements

## Review Checklist by Language

### Python Backend

| Check | Severity |
|-------|----------|
| Type annotations on public functions | Blocking |
| Pydantic v2 syntax (ConfigDict) | Blocking |
| No `except: pass` | Blocking |
| No `print()` statements | Blocking |
| Structured logging with loguru | Blocking |
| Input validation | Blocking |
| Encrypted sensitive data storage | Blocking |
| Async/await for I/O | Warning |
| Docstrings on functions | Suggestion |
| Service layer separation | Suggestion |

**Review Example**:

```markdown
## Code Review: backend/api/account.py

### Issues Found

#### 🔴 Blocking: Missing type annotation

**Location**: line 42

```python
async def delete_account(account_id, db):  # Missing types!
```

**Required Fix**:
```python
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
```

#### 🟡 Warning: Verbose error handling

**Location**: line 78

The error handling could be consolidated with a helper function.

---

**Verdict**: ❌ Changes Requested
**Blocking Issues**: 1
**Warnings**: 1
```

### TypeScript Frontend

| Check | Severity |
|-------|----------|
| No `any` types | Blocking |
| Error handling with AxiosError | Blocking |
| No `console.log` in production | Warning |
| Function components only | Warning |
| Props interface defined | Warning |
| useCallback for callbacks | Suggestion |
| Custom hooks for logic reuse | Suggestion |

**Review Example**:

```markdown
## Code Review: frontend/src/pages/AIClip.tsx

### Issues Found

#### 🔴 Blocking: `any` type in catch

**Location**: line 75

```typescript
} catch (error: any) {  // VIOLATION: any type
  message.error('获取视频信息失败')
}
```

**Required Fix**:
```typescript
import { AxiosError } from 'axios'

} catch (error: unknown) {
  if (error instanceof AxiosError) {
    message.error(error.response?.data?.detail || '请求失败')
  } else {
    message.error('未知错误')
  }
}
```

---

**Verdict**: ❌ Changes Requested
**Blocking Issues**: 1
```

## Security Review

### Check for Exposed Secrets

- Search for `password`, `api_key`, `secret`, `token` in code
- Check `.env` is in `.gitignore`
- Verify no default credentials

### Check for Injection Vulnerabilities

- SQL queries use ORM
- File paths are validated
- No `eval()` usage

### Check for Data Exposure

- Response models exclude sensitive fields
- Cookies/passwords not returned to client
- Error messages don't expose internals

**Review Example**:

```markdown
## Security Review

### ✅ Passed Checks

- [x] No hardcoded secrets
- [x] Cookies encrypted in storage
- [x] Response excludes sensitive fields
- [x] Input validation present

### 🔴 Critical Issue Found

**Issue**: Exposing internal error details

**Location**: backend/api/account.py:45

```python
except Exception as e:
    logger.error(f"DB Error: {e}")  # Exposing internals
    raise HTTPException(status_code=500, detail=str(e))
```

**Fix**:
```python
except Exception as e:
    logger.error("账号创建失败: error_type={}", type(e).__name__)
    raise HTTPException(status_code=500, detail="服务器内部错误")
```

---

**Security Verdict**: ❌ Vulnerable
```

## Architecture Review

For significant changes, also check:

- [ ] API contracts are consistent
- [ ] No circular dependencies
- [ ] Service layer properly separated
- [ ] Database migrations are reversible
- [ ] Performance considerations addressed

## Review Response Format

```markdown
## Code Review Response

### Author: [Name]
### Reviewer: [Name]
### Date: YYYY-MM-DD
### Files Reviewed: [List]

### Summary

[Brief description of what was reviewed and overall assessment]

### Blocking Issues

1. [Issue description with location and fix required]

### Warnings

1. [Warning description with suggestion]

### Approved Sections

[Sections that are good and don't need changes]

### Verdict

- ❌ Changes Requested
- ⚠️ Approved with Comments
- ✅ Approved

### Next Steps

[What author should do next]
```

## Rationale

These rules ensure:
- Consistent code quality across the codebase
- Security vulnerabilities are caught before deployment
- Knowledge sharing through code review
- Maintainable code through documented standards

## Related Rules

- `python-coding-rules.md` — Specific Python rules
- `typescript-coding-rules.md` — Specific TypeScript rules
- `security-rules.md` — Security requirements
