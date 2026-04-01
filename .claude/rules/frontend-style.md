---
paths:
  - "frontend/src/**/*.tsx"
  - "frontend/src/**/*.ts"
---

# Frontend Style Guide

TypeScript and React coding standards for the 得物掘金工具 frontend.

## Rule Statements

- TypeScript interfaces MUST be defined for all component props
- React components MUST use functional component syntax
- State management MUST use Zustand store for global state
- API calls MUST handle loading and error states
- Components MUST use Ant Design components when available
- CSS MUST use Tailwind classes or component-scoped styles

## Rationale

Consistent typing prevents runtime errors. Functional components with hooks are the modern React standard. Zustand provides simple, performant state management. Ant Design ensures UI consistency.

## Examples

**Correct**:

```typescript
interface AccountCardProps {
  account: Account;
  onLogin: () => void;
  onLogout: () => void;
}

export const AccountCard: React.FC<AccountCardProps> = ({
  account,
  onLogin,
  onLogout,
}) => {
  const [loading, setLoading] = useState(false);

  if (loading) return <Spin />;

  return <Card>{account.name}</Card>;
};
```

**Incorrect**:

```typescript
// Missing types, using 'any'
export const AccountCard = (props: any) => {
  const [loading, setLoading] = useState(false);

  return <Card>{props.account.name}</Card>;
};
```

## Related Rules

- `typescript-guards.md` — TypeScript type guards
- `security.md` — Security considerations
