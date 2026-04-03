# ADR-008: 得物账号 vs 系统用户 - 概念澄清

**状态**: Accepted

**日期**: 2026-04-02

**审查者**: Tech Lead

---

## 背景

在设计 DewuGoJin 系统时，发现存在两类不同的"账号"和"登录"概念，容易造成混淆：

1. **系统用户** - 使用 DewuGoJin 系统的人
2. **得物账号** - 得物平台的账号，是系统的外部资源

---

## 决策

### 明确两类概念

| 概念 | 英文术语 | 说明 | 状态 |
|-----|---------|------|------|
| **系统用户** | System User | 多用户权限系统 | **暂不考虑** |
| **系统认证** | System Auth | 系统用户的登录认证 | **暂不考虑** |
| **得物账号** | Dewu Account | 得物平台账号 | **核心功能** |
| **得物连接** | Dewu Connection | 后端与得物平台的连接状态 | **核心功能** |

### 术语对照

| 旧术语（混淆） | 新术语（清晰） | 说明 |
|---------------|---------------|------|
| ~~系统登录~~ | ~~System Login~~ | 暂不考虑 |
| 账号登录 | 建立连接 (Establish Connection) | 与得物平台建立会话 |
| 登出 | 断开连接 (Close Connection) | 关闭与得物平台的会话 |
| 登录状态 | 连接状态 (Connection Status) | 在线/离线/过期 |
| 登录按钮 | 连接按钮 (Connect Button) | UI 按钮文案 |

### API 端点重命名

| 旧端点 | 新端点 | 说明 |
|-------|--------|------|
| `POST /accounts/login/{id}` | `POST /accounts/connect/{id}` | 建立连接 |
| `GET /accounts/login/{id}/stream` | `GET /accounts/connect/{id}/stream` | SSE 连接状态 |
| `POST /accounts/logout/{id}` | `POST /accounts/disconnect/{id}` | 断开连接 |

### 前端组件重命名

| 旧组件 | 新组件 | 说明 |
|-------|--------|------|
| `LoginModal.tsx` | `ConnectionModal.tsx` | 连接弹窗 |

---

## 影响

### 需要修改的文件

| 文件 | 修改内容 |
|------|---------|
| `backend/api/account.py` | 端点重命名 |
| `backend/core/dewu_client.py` | 方法命名 |
| `frontend/src/components/LoginModal.tsx` | 组件重命名 |
| `frontend/src/pages/Account.tsx` | 文案修改 |
| `docs/architecture.md` | 文档更新 |

### API 兼容性

- **Breaking Change**: 需要更新所有调用方
- 建议同时支持旧端点作为别名

---

## 后续行动

| 优先级 | 行动 | 负责人 |
|--------|------|--------|
| 高 | 更新后端 API 端点命名 | Backend Lead |
| 高 | 更新前端组件和文案 | Frontend Lead |
| 中 | 更新 CLI 设计方案 | Tech Lead |
| 低 | 更新文档 | - |

---

## 参考

- [ADR-007: API 测试 CLI 技术选型](./ADR-007-api-test-cli.md)
- [得物掘金工具架构文档](../architecture.md)
