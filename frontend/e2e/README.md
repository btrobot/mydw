# E2E Testing Guide

得物掘金工具 - 端到端测试指南

## 概述

本目录包含使用 Playwright 编写的 E2E（End-to-End）测试用例。测试使用与后端自动化相同的 Patchright 浏览器引擎，以获得最佳的反检测效果。

## 测试用例

### TEST-LOGIN-01: 登录功能测试

| 测试ID | 测试名称 | 描述 |
|--------|----------|------|
| TEST-LOGIN-01-01 | Login modal opens correctly | 验证登录弹窗正确打开 |
| TEST-LOGIN-01-02 | Modal can be closed and reopened | 验证弹窗可以关闭和重新打开 |
| TEST-LOGIN-02-01 | Phone number format validation | 验证手机号格式校验 |
| TEST-LOGIN-02-02 | Empty verification code validation | 验证验证码非空校验 |
| TEST-LOGIN-03-01 | Login form submission | 验证表单提交 |
| TEST-LOGIN-03-02 | Code sending | 验证验证码发送 |
| TEST-LOGIN-04-01 | Login with wrong code | 验证错误验证码处理 |
| TEST-LOGIN-04-02 | Login with empty fields | 验证空字段处理 |
| TEST-LOGIN-05-01 | Session export/import | 验证会话导出导入 |
| TEST-LOGIN-05-02 | Session file persistence | 验证会话文件持久化 |
| TEST-LOGIN-06-01 | SSE connection | 验证 SSE 连接 |
| TEST-LOGIN-06-02 | SSE status updates | 验证 SSE 状态更新 |
| TEST-LOGIN-07-01 | Form input labels | 验证表单标签可访问性 |
| TEST-LOGIN-07-02 | Button keyboard access | 验证按钮键盘可访问性 |

## 前置条件

### 1. 安装依赖

```bash
# 安装 Playwright 测试框架
npm install -D @playwright/test

# 安装 Playwright 浏览器（如果使用默认浏览器）
npx playwright install chromium

# 或者安装 Patchright 浏览器（推荐 - 与后端相同）
npm install -D patchright
npx playwright install chromium  # patchright 会自动使用 patchright 的 chromium
```

### 2. 启动服务

测试需要以下服务运行：

- **前端**: http://localhost:5173
- **后端 API**: http://localhost:8000

可以使用以下方式启动：

```bash
# 方式 1: 手动启动
# 终端 1: 启动后端
cd ../backend
python -m uvicorn main:app --reload --port 8000

# 终端 2: 启动前端
cd frontend
npm run dev

# 方式 2: 使用 Playwright 的 webServer 配置自动启动
npx playwright test --project=chromium
```

### 3. 配置测试数据

确保后端 API 可用，测试会自动创建和清理测试账号。

## 运行测试

### 运行所有测试

```bash
cd frontend
npx playwright test
```

### 运行特定测试文件

```bash
npx playwright test e2e/login/login.spec.ts
```

### 运行特定测试用例

```bash
# 按测试 ID 运行
npx playwright test --grep "TEST-LOGIN-01"

# 按描述运行
npx playwright test --grep "Login modal opens correctly"
```

### 在有头模式下运行

```bash
npx playwright test --project=chromium-headed
```

### 生成测试报告

```bash
# 生成 HTML 报告
npx playwright test --reporter=html

# 报告将保存在 e2e/reports 目录
```

### 查看测试跟踪

失败测试的跟踪文件保存在 `test-results` 目录：

```bash
# 查看特定测试的跟踪
npx playwright show-trace test-results/login-xxx/trace.zip
```

## 调试

### 开启调试模式

```bash
# 逐行执行测试
npx playwright test --debug

# 或者设置环境变量
DEBUG=pw:* npx playwright test
```

### 在浏览器中打开测试

```bash
# 显示浏览器窗口，逐个执行测试
npx playwright test --headed

# 暂停在第一个失败点
npx playwright test --headed --pause-on-first-failure
```

### 检查元素选择器

```bash
# 使用 Playwright Inspector
npx playwright open http://localhost:5173
```

## 测试配置

### 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| E2E_BASE_URL | http://localhost:5173 | 前端 URL |
| E2E_API_URL | http://localhost:8000 | 后端 API URL |
| CI | - | 是否在 CI 环境中运行 |

### Playwright 配置文件

主配置文件: `e2e/playwright.config.ts`

关键配置项：
- `testDir`: 测试文件目录
- `projects`: 浏览器配置
- `webServer`: 自动启动服务配置
- `reporter`: 测试报告格式

## 测试数据结构

```
frontend/e2e/
├── playwright.config.ts   # Playwright 配置
├── setup.ts               # 全局设置
├── teardown.ts            # 全局清理
├── test-data/             # 测试数据目录
│   └── session.json       # 会话数据
├── reports/               # 测试报告目录
│   └── index.html        # HTML 报告
├── login/
│   └── login.spec.ts      # 登录测试用例
└── README.md              # 本文件
```

## 常见问题

### 1. 测试超时

如果遇到超时错误：
- 检查服务是否正常运行
- 增加超时时间（修改 `playwright.config.ts` 中的 `actionTimeout` 和 `navigationTimeout`）

### 2. 找不到元素

如果元素选择器失效：
- 检查页面是否完全加载（使用 `waitForLoadState('networkidle')`）
- 使用 `waitForSelector()` 等待元素出现
- 更新选择器（可能 UI 发生了变化）

### 3. SSE 连接失败

如果 SSE 测试失败：
- 检查后端是否支持 SSE
- 检查 `/api/accounts/login/{id}/stream` 端点是否可用

### 4. 会话测试失败

如果会话持久化测试失败：
- 确保测试数据目录有写权限
- 检查 Cookie 和存储是否正确配置

## 持续集成

### GitHub Actions 示例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps chromium

      - name: Run E2E Tests
        run: |
          cd frontend
          npx playwright test --reporter=html

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/e2e/reports/
```

## 维护指南

### 添加新测试

1. 在对应的 `*.spec.ts` 文件中添加测试用例
2. 使用清晰的测试 ID（如 `TEST-FEATURE-XX-XX`）
3. 添加适当的 `beforeEach` / `afterEach` 钩子
4. 确保测试清理自己的数据

### 更新选择器

如果 UI 发生变化：
1. 找到受影响的测试
2. 更新选择器为更稳定的选择器
3. 测试 `aria-label`, `data-testid` 等属性优先于类名

### 性能优化

- 使用 `test.describe.configure()` 设置并行模式
- 避免不必要的 `waitForTimeout()`
- 使用 `page.route()` 拦截不需要的请求

## 联系我们

如有问题，请联系 QA Lead 或在 GitHub Issue 中反馈。
