---
paths:
  - "frontend/src/**/*.ts"
  - "frontend/src/**/*.tsx"
---

# Frontend Coding Rules

适用于 `frontend/src/` 目录下的所有 TypeScript/React 代码。

## Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.x | UI Framework |
| TypeScript | 5.x | Type Safety |
| Ant Design | 5.x | Component Library |
| Zustand | 4.x | State Management |
| Axios | 1.x | HTTP Client |
| React Router | 6.x | Routing |
| Vite | 5.x | Build Tool |
| Electron | 28.x | Desktop Framework |

---

## 1. Type Safety

- MUST NOT use `any` type — use `unknown` with type guards instead
- MUST NOT use `as any` type assertions
- MUST NOT use non-null assertion operator `!`
- interface SHOULD be used for object shapes, type for unions/mappings
- generic types SHOULD be used for reusable components

### Type Guard Pattern

**Correct**:

```typescript
import { AxiosError } from 'axios'

// Type guard for Axios errors
function isAxiosError(error: unknown): error is AxiosError {
  return error instanceof AxiosError
}

// Usage
try {
  await api.get('/accounts')
} catch (error: unknown) {
  if (isAxiosError(error)) {
    message.error(error.response?.data?.detail || '请求失败')
  } else {
    message.error('未知错误')
  }
}
```

**Incorrect**:

```typescript
// VIOLATION: any type
function processData(data: any): any {
  return data.value
}

// VIOLATION: catch with any
} catch (error: any) {
  message.error(error.message)
}
```

### Generic Types

**Correct**:

```typescript
// Generic API fetcher
async function fetchData<T>(url: string): Promise<T> {
  const response = await api.get<T>(url)
  return response.data
}

// Usage
const accounts = await fetchData<Account[]>('/accounts')
const task = await fetchData<Task>('/tasks/1')
```

---

## 2. React Components

- components MUST be function components (not class components)
- components MUST define Props interface
- component props SHOULD use destructuring
- components SHOULD be small and focused (< 100 lines)

### Component Structure

**Correct**:

```typescript
// Props interface at top
interface AccountCardProps {
  account: Account
  onEdit: (id: number) => void
  onDelete: (id: number) => void
}

// Component name matches file name
export function AccountCard({ account, onEdit, onDelete }: AccountCardProps) {
  return (
    <Card>
      <h3>{account.name}</h3>
      <span>{account.status}</span>
      <Button onClick={() => onEdit(account.id)}>编辑</Button>
      <Button onClick={() => onDelete(account.id)} danger>删除</Button>
    </Card>
  )
}
```

**Incorrect**:

```typescript
// VIOLATION: class component
class AccountCard extends React.Component { ... }

// VIOLATION: missing props interface
export function AccountCard(props) {
  return <div>{props.account.name}</div>
}

// VIOLATION: component too large (should split)
```

### Component Composition

**Correct**:

```typescript
// Split large components
function AccountList() {
  return (
    <div>
      <AccountFilter />
      <AccountTable />
      <AccountPagination />
    </div>
  )
}
```

---

## 3. React Hooks

- custom hooks SHOULD encapsulate reusable stateful logic
- useCallback SHOULD be used for functions passed as props
- useMemo SHOULD be used for expensive computations
- useEffect cleanup functions MUST return cleanup function
- dependency arrays MUST be complete

### Custom Hooks

**Correct**:

```typescript
// Custom hook for async operations
function useAsync<T>(asyncFn: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await asyncFn()
      setData(result)
    } catch (err) {
      if (err instanceof AxiosError) {
        setError(err.response?.data?.detail || '请求失败')
      } else {
        setError('未知错误')
      }
    } finally {
      setLoading(false)
    }
  }, [asyncFn])

  return { data, loading, error, execute }
}
```

### useCallback Usage

**Correct**:

```typescript
// useCallback for callbacks passed to children
const handleEdit = useCallback((id: number) => {
  setEditingId(id)
}, [])

const handleDelete = useCallback(async (id: number) => {
  await accountService.delete(id)
  await refetch()
}, [refetch])

// Use in children
<AccountCard onEdit={handleEdit} onDelete={handleDelete} />
```

**Incorrect**:

```typescript
// VIOLATION: inline function in JSX causes re-renders
<AccountCard onEdit={(id) => setEditingId(id)} />

// VIOLATION: missing dependency
useEffect(() => {
  fetchData(id)
}, [id]) // Missing fetchData dependency
```

### useEffect Cleanup

**Correct**:

```typescript
useEffect(() => {
  const subscription = subscribe(handler)

  // Cleanup function
  return () => {
    subscription.unsubscribe()
  }
}, [handler])
```

---

## 4. Ant Design Components

- ConfigProvider SHOULD wrap the app for theme configuration
- Table components SHOULD use generic type parameter
- Form components SHOULD use Form.useForm() hook
- Modal components SHOULD use destroyOnClose for sensitive content

### ConfigProvider Setup

**Correct**:

```typescript
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'

const theme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
    fontSize: 14,
  },
  components: {
    Button: { controlHeight: 36 },
    Table: { headerBg: '#fafafa' },
  },
}

function App() {
  return (
    <ConfigProvider theme={theme} locale={zhCN}>
      {children}
    </ConfigProvider>
  )
}
```

### Table with Types

**Correct**:

```typescript
<Table<Account>
  dataSource={accounts}
  rowKey="id"
  columns={[
    { title: '账号', dataIndex: 'name', key: 'name' },
    {
      title: '状态',
      dataIndex: 'status',
      render: (status) => <StatusTag status={status} />
    },
    {
      title: '操作',
      render: (_, record) => (
        <Space>
          <Button onClick={() => onEdit(record.id)}>编辑</Button>
          <Button danger onClick={() => onDelete(record.id)}>删除</Button>
        </Space>
      )
    },
  ]}
  pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
  loading={loading}
/>
```

### Form with Hook

**Correct**:

```typescript
import { Form, Input, Button } from 'antd'

interface FormValues {
  name: string
  email: string
}

function AccountForm() {
  const [form] = Form.useForm<FormValues>()

  const onFinish = (values: FormValues) => {
    console.log(values)
  }

  return (
    <Form form={form} onFinish={onFinish} layout="vertical">
      <Form.Item
        name="name"
        label="名称"
        rules={[{ required: true, message: '请输入名称' }]}
      >
        <Input placeholder="请输入" />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit">提交</Button>
      </Form.Item>
    </Form>
  )
}
```

---

## 5. Zustand State Management

- stores SHOULD follow single responsibility principle
- store actions SHOULD handle loading and error states
- related state SHOULD be grouped in same store
- store selectors SHOULD use shallow comparison when needed

### Store Definition

**Correct**:

```typescript
// stores/accountStore.ts
import { create } from 'zustand'
import type { Account, CreateAccountDTO } from '../types'

interface AccountState {
  // State
  accounts: Account[]
  loading: boolean
  error: string | null

  // Actions
  fetchAccounts: () => Promise<void>
  createAccount: (data: CreateAccountDTO) => Promise<void>
  deleteAccount: (id: number) => Promise<void>
}

export const useAccountStore = create<AccountState>((set, get) => ({
  accounts: [],
  loading: false,
  error: null,

  fetchAccounts: async () => {
    set({ loading: true, error: null })
    try {
      const res = await accountService.list()
      set({ accounts: res.data, loading: false })
    } catch (err) {
      const message = err instanceof AxiosError
        ? err.response?.data?.detail || '获取失败'
        : '网络错误'
      set({ error: message, loading: false })
    }
  },

  deleteAccount: async (id) => {
    await accountService.delete(id)
    set({ accounts: get().accounts.filter(a => a.id !== id) })
  },
}))
```

### State Management Hierarchy

| State Scope | Storage Location | Example |
|------------|-----------------|---------|
| Component local | useState | form input |
| Shared across components | Zustand store | user data, settings |
| Form state | Ant Design Form | form.getFieldsValue() |
| URL / navigation | React Router | useParams, useSearchParams |
| Server state | React Query / SWR | (future) |

---

## 6. API Services

- API calls MUST use typed responses
- Axios instance MUST be configured with interceptors
- services SHOULD be module per resource
- environment variables MUST use VITE_ prefix

### API Instance

**Correct**:

```typescript
// services/api.ts
import axios, { type AxiosInstance, type AxiosError } from 'axios'

export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface ApiError {
  detail: string
}

export const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor
api.interceptors.request.use((config) => {
  // Add auth token if needed
  // const token = getToken()
  // if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    const message = error.response?.data?.detail || error.message
    return Promise.reject(new Error(message))
  }
)
```

### Service Module

**Correct**:

```typescript
// services/accountService.ts
import { api } from './api'
import type { Account } from '../types'

export const accountService = {
  list: () => api.get<Account[]>('/accounts'),

  get: (id: number) => api.get<Account>(`/accounts/${id}`),

  create: (data: CreateAccountDTO) =>
    api.post<Account>('/accounts', data),

  update: (id: number, data: UpdateAccountDTO) =>
    api.put<Account>(`/accounts/${id}`, data),

  delete: (id: number) =>
    api.delete(`/accounts/${id}`),
}
```

---

## 7. React Router

- routes SHOULD be defined in App.tsx or dedicated router file
- path parameters SHOULD have corresponding param types
- protected routes SHOULD use authentication check
- 404 routes SHOULD be handled

### Route Definition

**Correct**:

```typescript
// App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="account" element={<Account />} />
          <Route path="account/:id" element={<AccountDetail />} />
          <Route path="task" element={<Task />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
```

### Route Params

**Correct**:

```typescript
// Route with params
<Route path="account/:id" element={<AccountDetail />} />

// Component using params
function AccountDetail() {
  const { id } = useParams<{ id: string }>()

  if (!id) return <Navigate to="/account" replace />

  return <div>Account ID: {id}</div>
}
```

---

## 8. Import Organization

- imports MUST follow this order: framework → types → internal → utils
- type imports SHOULD use `import type` syntax
- path aliases MUST be used (@/ for src/)
- blank lines SHOULD separate import groups

**Correct**:

```typescript
// 1. React / framework
import React, { useState, useEffect, useCallback } from 'react'
import { Button, Card, Table, Space } from 'antd'

// 2. Types
import type { AxiosError } from 'axios'
import type { Account, Task } from '@/types'

// 3. Internal modules
import { api } from '@/services/api'
import { accountService } from '@/services/accountService'
import { useAccountStore } from '@/stores/accountStore'

// 4. Utils
import { formatDate } from '@/utils/format'
import { validateEmail } from '@/utils/validation'
```

**Incorrect**:

```typescript
// VIOLATION: wrong order
import { formatDate } from '@/utils/format'
import { useState } from 'react'
import { accountService } from '@/services/accountService'
```

---

## 9. Project Structure

```
frontend/src/
├── components/           # Shared components
│   ├── Layout.tsx       # App layout with sidebar
│   ├── StatusTag.tsx    # Reusable UI components
│   └── Empty.tsx
├── pages/               # Page components
│   ├── Dashboard.tsx
│   ├── Account.tsx
│   ├── Task.tsx
│   ├── Material.tsx
│   ├── AIClip.tsx
│   └── Settings.tsx
├── services/           # API services
│   ├── api.ts          # Axios instance
│   ├── accountService.ts
│   ├── taskService.ts
│   └── materialService.ts
├── stores/             # Zustand stores
│   ├── accountStore.ts
│   └── taskStore.ts
├── hooks/              # Custom hooks
│   ├── useAsync.ts
│   └── usePermission.ts
├── types/              # Type definitions
│   └── index.ts
├── utils/              # Utility functions
│   └── format.ts
├── App.tsx
└── main.tsx
```

---

## 10. Prohibited Patterns

- MUST NOT use `any` type
- MUST NOT use `as any` type assertions
- MUST NOT use non-null assertion `!`
- MUST NOT use `var` — use `const` or `let`
- MUST NOT use `==` or `!=` — use `===` or `!==`
- MUST NOT use `console.log` in production code
- MUST NOT use `eval()` or `new Function()`
- MUST NOT use class components
- MUST NOT create functions inside render JSX
- MUST NOT use `innerHTML` — use `textContent`
- MUST NOT use relative API paths (`/api/...`) — use `API_BASE` or `api` instance
- MUST NOT use `BrowserRouter` — use `HashRouter` (Electron `file://` compatibility)

---

## 11. Electron Compatibility

This app runs in Electron with `file://` protocol. These rules prevent common breakage:

### API Requests

All HTTP requests MUST use absolute URLs via `API_BASE` or the `api` axios instance.

- `api` axios instance (from `@/services/api`) has `baseURL` configured — use for standard requests
- `API_BASE` constant (from `@/services/api`) — use for non-axios calls (EventSource, raw fetch)

**Correct**:

```typescript
import { api, API_BASE } from '@/services/api'

// axios — uses baseURL automatically
const { data } = await api.get('/accounts')

// EventSource — must use API_BASE
const es = new EventSource(`${API_BASE}/accounts/connect/${id}/stream`)

// Raw fetch — must use API_BASE
const res = await fetch(`${API_BASE}/system/health`)
```

**Incorrect**:

```typescript
// VIOLATION: relative path resolves to file:///E:/api/... in Electron
const es = new EventSource(`/api/accounts/connect/${id}/stream`)
await axios.post(`/api/accounts/connect/${id}/send-code`, body)
await fetch('/api/system/health')
```

### Routing

MUST use `HashRouter` (not `BrowserRouter`). `BrowserRouter` requires server-side routing which doesn't work under `file://` protocol.

**Correct**:

```typescript
import { HashRouter } from 'react-router-dom'
// URLs: file:///path/index.html#/dashboard
```

**Incorrect**:

```typescript
// VIOLATION: causes white screen in Electron production build
import { BrowserRouter } from 'react-router-dom'
```

### Vite Base Path

Production builds for Electron MUST use relative base path (`./`). Set via `ELECTRON_BUILD=true` env variable which triggers `base: './'` in `vite.config.ts`.

---

## Rationale

These rules ensure:
- Type safety prevents runtime errors
- Consistent React patterns improve maintainability
- Proper hook usage optimizes performance
- Ant Design best practices improve UX
- State management hierarchy prevents data duplication
- Clean import organization improves readability

## Related Rules

- `electron-rules.md` — Electron security configuration
- `security-rules.md` — General security requirements
- `api-design-rules.md` — API contract patterns
- `code-review-rules.md` — Code review checklist
