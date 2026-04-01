---
paths:
  - "frontend/**/*.ts"
  - "frontend/**/*.tsx"
---

# TypeScript Style - TypeScript 代码风格

适用于 `frontend/` 目录。

## 基本原则

1. **严格类型**: 禁止使用 `any`
2. **显式优于隐式**: 类型明确声明
3. **不可变性**: 优先使用 `const`
4. **函数式**: 优先使用纯函数

## 类型定义

### 接口 vs 类型别名

**Correct**:

```typescript
// ✅ 接口：描述对象结构
interface User {
  id: number
  name: string
  email: string
}

// ✅ 类型别名：联合类型、映射类型
type Status = 'pending' | 'active' | 'inactive'
```

**Incorrect**:

```typescript
// ❌ 类型别名描述对象（除非需要泛型）
type User = { id: number; name: string }  // 用接口代替
```

### 禁止 any

**Correct**:

```typescript
// ✅ 正确：使用具体类型
interface Data {
  value: string
}

function processData(data: Data): string {
  return data.value
}

// ✅ 如果真的不确定类型
function processData(data: unknown): string {
  if (typeof data === 'object' && data !== null && 'value' in data) {
    return String((data as { value: string }).value)
  }
  throw new Error('Invalid data')
}
```

**Incorrect**:

```typescript
// ❌ 错误：使用 any
function processData(data: any): any {
  return data.value
}
```

## 函数

### 函数签名

**Correct**:

```typescript
// ✅ 正确：完整类型
type Handler = (event: Event) => void

// ✅ 正确：参数解构
function processAccount({ id, name, status = 'active' }: Account): void {
  // ...
}
```

**Incorrect**:

```typescript
// ❌ 错误：参数过多或缺少类型
function createUser(id, name, email, phone, address, ...): void
```

## React

### 组件定义

**Correct**:

```typescript
// ✅ 正确：Props 接口 + 函数组件
interface Props {
  title: string
  count?: number
  onClick: () => void
  data: Account[]
}

export function Component({ title, count = 0, onClick, data }: Props) {
  return (
    <div>
      <h1>{title}</h1>
      <span>{count}</span>
      <button onClick={onClick}>Click</button>
    </div>
  )
}
```

**Incorrect**:

```typescript
// ❌ 错误：class 组件
class MyComponent extends React.Component {
  // ...
}
```

### Hooks

**Correct**:

```typescript
// ✅ 正确：自定义 Hook
function useAccounts() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(false)

  const fetchAccounts = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get<Account[]>('/accounts')
      setAccounts(res.data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAccounts()
  }, [fetchAccounts])

  return { accounts, loading, refetch: fetchAccounts }
}
```

**Incorrect**:

```typescript
// ❌ 错误：class 组件混用状态
class AccountManager extends React.Component {
  // 不要使用 class 组件
}
```

## Import 顺序

**Correct**:

```typescript
// 1. React / 框架
import React, { useState, useEffect } from 'react'
import { Button, Card } from 'antd'

// 2. 类型
import type { Account } from '../types'

// 3. 内部模块
import { api } from '../services/api'

// 4. 工具函数
import { formatDate } from '../utils/format'
```

**Incorrect**:

```typescript
// ❌ 错误：乱序导入
import { formatDate } from '../utils/format'
import { useState } from 'react'
import type { Account } from '../types'
import { api } from '../services/api'
```

## 禁止的模式

- ❌ `any`
- ❌ `as any`
- ❌ `!` 非空断言
- ❌ `var`
- ❌ `==` / `!=`（使用 `===`）
- ❌ `console.log`（生产环境）
- ❌ `eval`
