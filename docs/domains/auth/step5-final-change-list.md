# Step 5 最终变更清单

> 用途：作为 Step 5 的可提交交付清单，按 PR 分组列出主要文件与建议提交边界。

---

## 一、建议提交边界

### Commit 1 — PR1 auth observability

**后端**

- `backend/core/observability.py`
- `backend/core/auth_events.py`
- `backend/api/auth.py`
- `backend/services/auth_service.py`
- `backend/tests/test_auth_events_pr1.py`
- `backend/tests/test_auth_api.py`
- `backend/tests/test_auth_service.py`

**目的**

- 建立认证事件日志、trace context、hard-deny 追踪能力

---

### Commit 2 — PR2 auth metrics

**后端**

- `backend/core/auth_metrics.py`
- `backend/main.py`
- `backend/tests/test_auth_metrics_pr2.py`

**目的**

- 建立 auth metrics collector 和 `/metrics` 暴露

---

### Commit 3 — PR3 auth status API

**后端**

- `backend/api/auth.py`
- `backend/schemas/auth.py`
- `backend/services/auth_service.py`
- `backend/tests/test_auth_status_api_pr3.py`

**目的**

- 增加 status / health / session details API

---

### Commit 4 — PR4 auth error UX

**前端**

- `frontend/src/features/auth/AuthErrorBoundary.tsx`
- `frontend/src/features/auth/AuthErrorMessage.tsx`
- `frontend/src/features/auth/authErrorHandler.ts`
- `frontend/src/features/auth/useAuthStatus.ts`
- `frontend/src/features/auth/AuthProvider.tsx`
- `frontend/src/features/auth/LoginPage.tsx`
- `frontend/src/features/auth/AuthStatusPage.tsx`
- `frontend/src/features/auth/api.ts`
- `frontend/src/features/auth/types.ts`
- `frontend/src/features/auth/index.ts`
- `frontend/src/App.tsx`
- `frontend/e2e/auth-error-ux/auth-error-ux.spec.ts`
- `frontend/e2e/auth-bootstrap/auth-bootstrap.spec.ts`

**目的**

- 统一 auth 错误展示、bootstrap 错误 UX、登录错误 UX、状态页提示

---

### Commit 5 — PR5 auth admin

**后端**

- `backend/api/auth.py`
- `backend/services/auth_service.py`
- `backend/schemas/auth.py`
- `backend/tests/test_auth_admin_pr5.py`
- `backend/main.py`

**前端**

- `frontend/src/features/auth/api.ts`
- `frontend/src/features/auth/types.ts`
- `frontend/src/features/auth/admin/SessionAdmin.tsx`
- `frontend/src/features/auth/admin/SessionList.tsx`
- `frontend/src/features/auth/index.ts`
- `frontend/src/components/Layout.tsx`
- `frontend/src/App.tsx`
- `frontend/e2e/auth-admin/auth-admin.spec.ts`

**目的**

- 增加 auth admin 会话列表、revoke、前端管理页面与历史会话 revoke 保护

---

## 二、统一验证清单

### 后端回归

```bash
pytest backend/tests/test_auth_admin_pr5.py backend/tests/test_auth_status_api_pr3.py backend/tests/test_auth_api.py backend/tests/test_auth_service.py backend/tests/test_auth_metrics_pr2.py backend/tests/test_auth_events_pr1.py backend/tests/test_auth_grace_pr4.py backend/tests/test_auth_hard_deny_pr3.py -q
```

结果：

- **133 passed**

### 前端类型检查

```bash
cd frontend
npm run typecheck
```

结果：

- **PASS**

### 前端 E2E 回归

```bash
playwright test e2e/auth-bootstrap/auth-bootstrap.spec.ts e2e/auth-regression/auth-regression.spec.ts e2e/auth-shell/auth-shell.spec.ts e2e/auth-error-ux/auth-error-ux.spec.ts e2e/auth-admin/auth-admin.spec.ts
```

结果：

- **19 passed**

### 编译/诊断

- `python -m compileall`：PASS
- 受影响文件 diagnostics：0 errors

---

## 三、当前工作区说明

当前仓库 `git status` 仍显示大量改动与未跟踪文件，说明：

- Step 5 已实现完成
- 但尚未做最终提交整理

建议做法：

1. 仅按上面的 Step 5 清单筛选文件
2. 分 PR / 分主题提交
3. 不把与 Step 5 无关的历史工作区改动混进同一个提交

---

## 四、交付判断

Step 5 已具备：

- 可运行实现
- 对应测试
- E2E 回归
- 架构复审通过

因此可以进入：

- **提交整理**
- **PR 合并说明编写**
- **发布说明编写**
