---
paths:
  - "frontend/e2e/**/*.ts"
---

# E2E Testing Rules

适用于 `frontend/e2e/` 目录下的所有 Playwright 测试。

## 核心原则

**测试用例必须经过实际运行验证后才能提交。**

```markdown
# 禁止流程
Agent 写测试 → 直接提交 → CI 失败 → 修复

# 正确流程
Agent 写测试 → 开发者验证选择器 → 运行测试 → 通过后提交
```

---

## 1. 选择器验证（强制）

### 验证步骤

1. **编写前**：在浏览器 DevTools 中验证选择器是否能定位到目标元素
2. **编写后**：运行测试一次，确保选择器有效
3. **提交前**：测试必须通过

### DevTools 验证方法

```javascript
// 在浏览器控制台中使用
document.querySelector('button:has-text("取消")')
document.querySelector('.ant-modal button')
document.querySelector('tr:has-text("account_id")')
```

如果返回 `null`，选择器无效。

---

## 2. 常见陷阱（知识参考）

这些是经过验证的 Ant Design 组件渲染行为：

### 按钮类型

| Ant Design 组件 | 实际 HTML | 验证结果 |
|-----------------|-----------|----------|
| `<Button type="link">` | `<a>` | ✅ 是 `<a>` 不是 `<button>` |
| `<Button>` | `<button>` | ✅ 是 `<button>` |
| 文本 "取消" | - | ❌ 实际是 "取 消"（带空格） |

### 选择器建议

```typescript
// Ant Design link 按钮 - 用 a 或 link role
page.locator('a:has-text("登录")')
page.locator('a, button').filter({ hasText: '登录' })

// 模态框按钮 - 限定范围更稳定
page.locator('.ant-modal button:has-text("取 消")')
page.locator('.ant-modal button[type="submit"]')

// 表格行内按钮 - 需要行内定位
page.locator('tr').filter({ hasText: accountId })
  .locator('a, button').filter({ hasText: '登录' })
```

---

## 3. 选择器优先级

按可靠性排序：

| 优先级 | 选择器 | 说明 |
|--------|--------|------|
| 1 | `getByRole()` | 最可靠，基于无障碍属性 |
| 2 | `getByLabel()` | 表单输入 |
| 3 | `getByText()` | 可见文本 |
| 4 | `locator('a, button')` | 组合选择，灵活 |
| 5 | `.ant-xxx` class | 脆弱，慎用 |
| - | XPath | 禁止使用 |

---

## 4. 等待模式

### 优先使用

```typescript
// 等待元素出现
await page.waitForSelector('.ant-modal', { timeout: 5000 })

// 等待网络空闲（API 调用后）
await page.waitForLoadState('networkidle')

// 断言自带等待
await expect(locator).toBeVisible()
```

### 避免使用

```typescript
// 禁止 - 任意等待
await page.waitForTimeout(5000)
```

---

## 5. 动态元素处理

### 表格行

```typescript
// 正确 - 点击前重新查询
await page.locator('tr').filter({ hasText: accountId })
  .locator('a, button').filter({ hasText: '登录' })
  .click()

// 错误 - 可能产生 stale element
const row = page.locator(`tr:has-text("${accountId}")`)
const btn = row.locator('button')
await btn.click()  // row 可能已失效
```

### 模态框

```typescript
// 等待模态框出现
await page.waitForSelector('.ant-modal', { timeout: 5000 })

// 模态框内元素需要重新查询
await page.locator('.ant-modal button[type="submit"]').click()
```

---

## 6. 测试数据管理

### 正确方式

```typescript
// 在 beforeEach 中创建
test.beforeEach(async ({ page }) => {
  const accountId = await createTestAccount()
  // ...
})

// 在 afterEach 中清理
test.afterEach(async () => {
  await deleteTestAccount(accountId)
})
```

### 禁止

- 硬编码其他测试创建的数据 ID
- 依赖测试间的共享状态
- 在测试间手动创建/删除数据

---

## 7. URL 配置

```typescript
// 必须显式定义 BASE_URL
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'

// 使用显式 URL
await page.goto(BASE_URL)
await page.goto(`${BASE_URL}/account`)
```

---

## 8. 错误处理

```typescript
// 检查元素存在性时使用 catch
const hasError = await locator.isVisible().catch(() => false)
if (hasError) {
  await expect(locator).toBeVisible()
}
```

---

## 相关规则

- `typescript-coding-rules.md` - TypeScript 编码规范
- `code-review-rules.md` - 代码审查清单
