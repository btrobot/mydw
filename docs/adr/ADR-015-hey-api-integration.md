# ADR-015: Hey-API 自动生成前端 API Client

**状态**: 已批准

**日期**: 2026-04-01

**决策者**: Tech Lead

---

## 1. 背景

### 问题

1. 前端 API 手动编写，与后端类型不一致
2. 新增 API 需要两端同步修改
3. 缺乏类型安全保证

### 目标

实现从后端 OpenAPI Schema 自动生成前端类型安全 API Client。

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                          Backend                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │ FastAPI      │   │ Pydantic      │   │ OpenAPI Schema       │ │
│  │ Routes       │ → │ Schemas       │ → │ /openapi.json        │ │
│  └──────────────┘   └──────────────┘   └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓ fetch
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │ hey-api      │ → │ Generated    │ → │ React Query         │ │
│  │ Client       │   │ API Client    │   │ + Zustand Store     │ │
│  └──────────────┘   └──────────────┘   └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 技术选型

| 选项 | 决策 |
|------|------|
| **API 生成器** | hey-api (@hey-api/openapi-ts) |
| **HTTP Client** | @hey-api/client-fetch |
| **缓存层** | @tanstack/react-query |
| **枚举映射** | TypeScript enum |
| **生成目录** | src/api/ |

---

## 4. 依赖清单

```bash
# 安装依赖
npm install @hey-api/client-fetch @tanstack/react-query
npm install -D @hey-api/openapi-ts
```

---

## 5. 配置文件

### openapi.config.ts

```typescript
import type { ConfigFile } from '@hey-api/openapi-ts'

export default {
  input: 'http://127.0.0.1:8000/openapi.json',
  output: {
    path: './src/api',
    index: true,
  },
  client: '@hey-api/client-fetch',
  types: {
    enums: 'typescript',
  },
  services: {
    asClass: false,
  },
} satisfies ConfigFile
```

### vite.config.ts (更新)

添加 API 代理配置：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
},
```

---

## 6. NPM Scripts

```json
{
  "scripts": {
    "api:generate": "openapi-ts --config openapi.config.ts",
    "api:generate:watch": "openapi-ts --config openapi.config.ts --watch",
    "api:dev": "npm run api:generate && vite"
  }
}
```

---

## 7. 生成结构

```
src/api/
├── index.ts           # 主入口，导出所有服务
├── client.ts          # 底层 HTTP client
├── types.gen.ts      # 生成的类型定义（严格类型）
├── AccountService.ts  # 账号管理 API
├── TaskService.ts     # 任务管理 API
├── MaterialService.ts  # 素材管理 API
├── ProductService.ts  # 商品管理 API
├── PublishService.ts  # 发布控制 API
└── SystemService.ts   # 系统 API
```

---

## 8. 集成组件

### QueryProvider

位于 `src/providers/QueryProvider.tsx`

```tsx
export const QueryProvider = ({ children }) => {
  const [queryClient] = useState(
    new QueryClient({
      defaultOptions: {
        queries: { staleTime: 60 * 1000, retry: 1 },
        mutations: { retry: 0 },
      },
    })
  )
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
```

---

## 9. 使用方式

### 开发流程

```bash
# 1. 启动后端 (确保 OpenAPI 可访问)
cd backend && uvicorn main:app

# 2. 生成前端 API
npm run api:generate

# 3. 开发
npm run dev
```

### 组件中使用

```tsx
import { useAccounts, useCreateAccount } from '@/hooks/useApi'
import type { AccountCreate } from '@/api/types.gen'

function AccountList() {
  const { data: accounts, isLoading } = useAccounts()

  const createAccount = useCreateAccount({
    onSuccess: () => {
      // 乐观更新等
    },
  })

  const handleCreate = (data: AccountCreate) => {
    createAccount.mutate(data)
  }

  // ...
}
```

---

## 10. 类型安全保证

生成的 `types.gen.ts` 与后端 Pydantic 完全对应：

```typescript
// 后端
class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

// 前端 (自动生成)
export enum AccountStatus {
  Active = 'active',
  Inactive = 'inactive',
}
```

---

## 11. 向后兼容

保留现有 `src/services/api.ts` 作为 fallback。

新 API 客户端位于 `src/api/`，按需迁移。

---

## 12. 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| OpenAPI 不可用 | 后端启动后生成，或离线缓存 |
| 生成覆盖修改 | 不修改生成文件，使用 hooks 封装 |
| 后端 Schema 变更 | 重新生成即可 |

---

## 13. 决策记录

- 2026-04-01: 批准使用 hey-api + React Query 方案
