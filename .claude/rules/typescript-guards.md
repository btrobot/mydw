---
paths:
  - "frontend/src/**/*.ts"
  - "frontend/src/**/*.tsx"
---

# TypeScript Type Guards

TypeScript type safety standards for the 得物掘金工具 frontend.

## Rule Statements

- TypeScript type guards MUST be used when narrowing union types
- API response types MUST be validated with Zod or type guards
- Optional fields MUST be handled explicitly
- Type assertions (`as`) MUST be avoided except at trust boundaries
- Unknown data from external sources MUST be validated

## Rationale

Type guards prevent runtime errors from incorrect type assumptions. Validating API responses catches data mismatches early. Explicit optional handling prevents undefined errors. Avoiding assertions maintains type safety throughout the codebase.

## Examples

**Correct**:

```typescript
// Type guard for account status
function isActiveAccount(account: Account): account is ActiveAccount {
  return account.status === 'active';
}

// Using the guard
function handleAccount(account: Account | null) {
  if (!account) return <div>Loading...</div>;
  if (isActiveAccount(account)) {
    return <ActiveStatus lastLogin={account.lastLogin} />;
  }
  return <InactiveStatus />;
}

// API response validation
function isAccount(data: unknown): data is Account {
  return (
    typeof data === 'object' &&
    data !== null &&
    'id' in data &&
    'name' in data &&
    typeof (data as any).id === 'string'
  );
}
```

**Incorrect**:

```typescript
// Blindly assuming type
const account = data as Account;
console.log(account.lastLogin.toISOString()); // Could crash!

// Not handling optional fields
const name = account.optionalField.toUpperCase(); // Error if undefined

// Overusing assertions
const value = response.data as any as SpecificType;
```

## Related Rules

- `frontend-style.md` — Frontend conventions
- `security.md` — Security considerations
