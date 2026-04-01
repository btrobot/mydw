---
paths:
  - "backend/**/*.py"
  - "frontend/src/**/*.{ts,tsx}"
---

# Security Best Practices

Security standards for the 得物掘金工具 project.

## Rule Statements

### Backend (Python)

- Cookie and secrets MUST be encrypted (AES-256-GCM)
- SECRET_KEY MUST be loaded from environment variables
- Database queries MUST use parameterized queries (SQLAlchemy)
- File paths MUST be validated before access
- User input MUST be validated and sanitized

### Frontend (TypeScript)

- API calls MUST use HTTPS in production
- Sensitive data MUST NOT be stored in localStorage
- User input MUST be validated before sending to API
- DOM content MUST be sanitized before rendering

## Rationale

Encryption protects user credentials. Environment variables prevent secret leakage. Parameterized queries prevent SQL injection. Path validation prevents directory traversal. Input validation prevents XSS and injection attacks.

## Examples

**Correct** (Python):

```python
from cryptography.fernet import Fernet

class CookieManager:
    def __init__(self, secret_key: bytes):
        self.fernet = Fernet(secret_key)

    def encrypt(self, cookie: str) -> str:
        return self.fernet.encrypt(cookie.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        return self.fernet.decrypt(encrypted.encode()).decode()
```

**Incorrect**:

```python
# Storing secrets in code
SECRET = "hardcoded_secret_key"

# SQL injection vulnerable
query = f"SELECT * FROM accounts WHERE id = {user_id}"
```

**Correct** (TypeScript):

```typescript
// Using axios with proper error handling
const response = await axios.post('/api/accounts', {
  name: sanitizeInput(accountName),
});

// Validating before API call
if (!isValidAccountName(name)) {
  throw new Error('Invalid account name');
}
```

**Incorrect**:

```typescript
// Storing sensitive data in localStorage
localStorage.setItem('cookie', response.data.cookie);

// XSS vulnerable
element.innerHTML = userContent; // BAD!
element.textContent = userContent; // GOOD!
```

## Related Rules

- `frontend-style.md` — Frontend conventions
- `backend-style.md` — Backend conventions
