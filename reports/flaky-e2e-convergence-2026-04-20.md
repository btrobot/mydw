# PR-3 flaky E2E 收敛说明

- 日期：2026-04-20
- 关联规划：
  - `.omx/plans/archive/prd-release-hardening-runtime-acceptance-closeout.md`
  - `.omx/plans/archive/test-spec-release-hardening-runtime-acceptance-closeout.md`
- 结论：**通过**

---

## 1. 收敛目标

本轮针对 release hardening 里明确点名的 E2E 风险项：

- `frontend/e2e/task-diagnostics/task-diagnostics.spec.ts`

目标不是扩写新测试，而是把“最近一次回归里出现过 retry 后通过”的不稳定信号收敛为：

1. 根因可解释；
2. 运行入口可重复；
3. 重复执行不再建立在偶发 retry 之上；
4. 如有剩余风险，显式记录。

---

## 2. 实际复现结果

### 2.1 直接按旧习惯把 `E2E_BASE_URL` 指到 `http://127.0.0.1:4173`

复现结果：

- `task-diagnostics` 并不是偶发失败，而是**稳定失败**
- 页面实际打开的是**另一套应用：Remote Admin**
- 典型失败表现：
  - 根路由无法进入 `/#/creative/workbench`
  - `task-list-semantics` 找不到
  - `dashboard-publish-status-error` 找不到

失败页面快照显示：

- 标题：`Remote Admin`
- 内容：`Remote authorization console`

这说明先前所谓“flaky”并不主要是任务页逻辑抖动，而是**测试运行时命中了错误的前端服务**。

### 2.2 根因判断

根因收敛为：

1. 旧 E2E 基线默认依赖外部手动准备的前端服务；
2. 当本机 `4173` 端口被其他前端占用时，Playwright 仍然会连上一个“看起来可访问”的页面；
3. 由于页面不是当前仓库 frontend，测试断言会表现成：
   - 路由等待超时；
   - `data-testid` 消失；
   - retry 后仍失败或表现出“似乎 flaky”的错觉。

因此，这不是 task diagnostics 页面本身的业务异步问题，也不是 auth fixture 污染主导，而是**E2E 入口环境不确定**。

---

## 3. 本轮最小修复

修改文件：

- `frontend/e2e/playwright.config.ts`
- `frontend/e2e/auth-bootstrap/auth-bootstrap.spec.ts`
- `frontend/e2e/auth-error-ux/auth-error-ux.spec.ts`
- `frontend/e2e/auth-regression/auth-regression.spec.ts`
- `frontend/e2e/auth-routing/auth-routing.spec.ts`
- `frontend/e2e/auth-shell/auth-shell.spec.ts`
- `frontend/e2e/auth-transport/auth-transport.spec.ts`
- `frontend/e2e/auth-admin/auth-admin.spec.ts`
- `frontend/e2e/login/login.spec.ts`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `frontend/e2e/utils/creativeReviewMocks.ts`

修复策略：

1. 给 E2E 约定一个更明确的默认端口：
   - `127.0.0.1:4174`
2. 当未显式传入 `E2E_BASE_URL` 时：
   - 由 Playwright `webServer` **自动执行**
     - `npm run build`
     - `npm run preview -- --host 127.0.0.1 --port 4174`
3. `reuseExistingServer=false`
   - 避免误复用“端口是通的，但应用不是当前 frontend”的错误环境。
4. 将 E2E spec / helper 里的默认 `BASE_URL` 回退值从固定 `5173` 改为：
   - `process.env.E2E_BASE_URL || ''`
   - 让 `page.goto('/#/...')` / `page.goto('/')` 统一回落到 Playwright `use.baseURL`
   - 不再出现“config 走 4174，但局部 spec 仍偷偷指向 5173”的双入口分叉

这样收敛后：

- 测试入口由 config 与 spec/helper 共用一套入口约定；
- 端口冲突会变成显式启动错误，而不是伪装成页面 flaky；
- `task-diagnostics` 可以在同一套受控 preview 上重复执行。

---

## 4. 验证结果

### 4.1 目标套件重复执行验证

命令：

```powershell
cd frontend
.\node_modules\.bin\playwright.cmd test -c e2e/playwright.config.ts e2e/task-diagnostics/task-diagnostics.spec.ts --repeat-each=3
```

结果：

- `18 passed`

覆盖：

- `chromium`
- `chromium-headed`
- 每个用例重复执行 3 次

结论：

- `task-diagnostics` 当前已不依赖 retry 才通过；
- 在受控 preview 基线上可重复通过。

### 4.2 关联 auth 路由/登录基线回归

由于本轮修改的是 E2E 全局运行入口，再补跑一组与 auth shell/路由直接相关的套件，确认没有把入口稳定化修复引入新的回归。

命令：

```powershell
cd frontend
.\node_modules\.bin\playwright.cmd test -c e2e/playwright.config.ts e2e/login/login.spec.ts e2e/auth-routing/auth-routing.spec.ts
```

结果：

- `38 passed`

### 4.3 类型检查

命令：

```powershell
cd frontend
npm run typecheck
```

结果：

- 通过

### 4.4 受影响文件静态诊断

文件：

- `frontend/e2e/playwright.config.ts`
- `frontend/e2e/auth-bootstrap/auth-bootstrap.spec.ts`
- `frontend/e2e/login/login.spec.ts`
- `frontend/e2e/auth-routing/auth-routing.spec.ts`
- `frontend/e2e/utils/creativeReviewMocks.ts`

结果：

- LSP diagnostics `0 errors`

---

## 5. 结论

本轮 PR-3 的结论是：

> `task-diagnostics` 之前的“不稳定”主要由 **E2E 入口环境不确定 / 误连到其他前端服务** 引起，而不是任务诊断页面自身的产品逻辑 flake。

经过本轮收敛：

- [x] 根因已记录；
- [x] 目标套件重复执行通过；
- [x] E2E 运行入口改为受控、自举；
- [x] spec/helper 默认入口已与 Playwright `baseURL` 对齐；
- [x] 关联 auth 路由/登录基线通过；
- [x] 受影响配置文件无静态错误。

因此：

> **PR-3 可标记为完成。**

---

## 6. 剩余风险（Residual Risk）

当前仍有两点保留说明：

1. `webServer` 会在测试前执行 `npm run build`
   - 运行更稳定，但单次耗时会上升；
   - 这是有意识的 release-hardening 取舍。
2. 若调用者显式传入 `E2E_BASE_URL`
   - 仍需自己保证该 URL 指向的是**当前 frontend**；
   - 本轮修复只保证“默认入口”受控，不替调用者纠正手工指定的错误地址。

---

## 7. 本 PR 建议提交边界

建议仅提交：

- `frontend/e2e/playwright.config.ts`
- `frontend/e2e/auth-bootstrap/auth-bootstrap.spec.ts`
- `frontend/e2e/auth-error-ux/auth-error-ux.spec.ts`
- `frontend/e2e/auth-regression/auth-regression.spec.ts`
- `frontend/e2e/auth-routing/auth-routing.spec.ts`
- `frontend/e2e/auth-shell/auth-shell.spec.ts`
- `frontend/e2e/auth-transport/auth-transport.spec.ts`
- `frontend/e2e/auth-admin/auth-admin.spec.ts`
- `frontend/e2e/login/login.spec.ts`
- `frontend/e2e/creative-workbench/creative-workbench.spec.ts`
- `frontend/e2e/utils/creativeReviewMocks.ts`
- `reports/flaky-e2e-convergence-2026-04-20.md`

不混入：

- 页面功能改动；
- 额外 UI 调整；
- 与 E2E 入口稳定性无关的测试重写。
