# 应用登录链路时序图

本文描述的是**应用登录（`/api/auth/*`）**，不是业务账号连接（`/api/accounts/connect/*`）。

相关代码入口：

- 前端登录页：`frontend/src/features/auth/LoginPage.tsx`
- 前端 Auth Bootstrap：`frontend/src/features/auth/AuthProvider.tsx`
- 前端路由门禁：`frontend/src/features/auth/AuthRouteGate.tsx`
- 本地 API：`backend/api/auth.py`
- 本地编排：`backend/services/auth_service.py`

---

## 1. 启动恢复时序

```mermaid
sequenceDiagram
    autonumber
    participant U as 用户
    participant FE as Electron 前端
    participant AP as AuthProvider
    participant BE as 本地 FastAPI
    participant AS as AuthService
    participant ST as 本地 Session/Secret Store

    U->>FE: 打开应用
    FE->>AP: 启动 Auth Bootstrap
    AP->>BE: GET /api/auth/session
    BE->>AS: get_session_summary()
    AS->>ST: 读取本地 machine session + device_id
    ST-->>AS: 本地摘要
    AS-->>BE: LocalAuthSessionSummary
    BE-->>AP: auth_state / device_id / expires_at ...

    AP->>BE: GET /api/auth/status
    BE->>AS: get_status()
    AS->>AS: restore_session()
    AS->>ST: 校验本地 session / refresh token / device_id
    AS-->>BE: AuthStatusResponse
    BE-->>AP: is_authenticated / requires_reauth / can_run_protected_actions ...

    AP->>FE: 写入当前 authState
    FE->>FE: AuthRouteGate 决定路由
    alt authenticated_active
        FE-->>U: 进入受保护主界面
    else authenticated_grace
        FE-->>U: 进入宽限模式界面
    else revoked / device_mismatch / expired
        FE-->>U: 跳转对应状态页
    else unauthenticated
        FE-->>U: 跳转 /login
    end
```

---

## 2. 登录提交时序

```mermaid
sequenceDiagram
    autonumber
    participant U as 用户
    participant FE as LoginPage
    participant DV as device.ts
    participant BE as 本地 FastAPI
    participant AS as AuthService
    participant RA as 远端认证系统
    participant ST as 本地 Session/Secret Store

    U->>FE: 输入 username / password
    FE->>DV: 获取或生成 device_id
    DV-->>FE: device_id
    FE->>BE: POST /api/auth/login\n{ username, password, device_id, client_version }
    BE->>AS: login(...)
    AS->>ST: 读取/固化本机 device_id
    AS->>ST: session.auth_state = authorizing
    AS->>RA: 远端 login(username, password, device_id, client_version)

    alt 远端登录成功
        RA-->>AS: access_token / refresh_token / user / entitlements / expires_at / offline_grace_until
        AS->>ST: 原子保存 access_token + refresh_token
        AS->>ST: 更新 machine session\n(authenticated_active, device_id, entitlements, expires_at ...)
        AS-->>BE: LocalAuthSessionSummary(authenticated_active)
        BE-->>FE: 登录成功摘要
        FE->>FE: 更新 session
        FE-->>U: 进入受保护主界面
    else 远端拒绝
        RA-->>AS: error_code(device_mismatch / revoked / disabled / token_expired ...)
        AS->>ST: 更新 auth_state / denial_reason
        AS-->>BE: HTTP error
        BE-->>FE: 错误响应
        FE-->>U: 留在登录页或跳到状态页
    else 远端网络失败
        RA-->>AS: transport error
        AS->>ST: auth_state = error
        AS-->>BE: 503 / transport error
        BE-->>FE: 错误响应
        FE-->>U: 显示网络/服务错误
    end
```

---

## 3. 刷新与宽限时序

```mermaid
sequenceDiagram
    autonumber
    participant FE as 前端/Transport Sync
    participant BE as 本地 FastAPI
    participant AS as AuthService
    participant RA as 远端认证系统
    participant ST as 本地 Session/Secret Store

    FE->>BE: POST /api/auth/refresh
    BE->>AS: refresh_if_needed()
    AS->>ST: 读取 refresh_token + 当前 machine session

    alt refresh 成功
        AS->>RA: refresh(refresh_token, device_id, client_version)
        RA-->>AS: 新 token + 新 session payload
        AS->>ST: 原子更新 token
        AS->>ST: auth_state = authenticated_active
        AS-->>BE: LocalAuthSessionSummary
        BE-->>FE: refreshed summary
    else 远端拒绝
        AS->>RA: refresh(...)
        RA-->>AS: revoked / device_mismatch / token_expired ...
        AS->>ST: 更新为 revoked / device_mismatch / expired
        AS-->>BE: HTTP error
        BE-->>FE: requires_reauth
    else 网络失败但 grace 仍有效
        AS->>RA: refresh(...)
        RA-->>AS: transport error
        AS->>ST: auth_state = authenticated_grace
        AS-->>BE: LocalAuthSessionSummary(authenticated_grace)
        BE-->>FE: grace summary
    else 网络失败且 grace 已失效
        AS->>RA: refresh(...)
        RA-->>AS: transport error
        AS->>ST: auth_state = expired
        AS-->>BE: LocalAuthSessionSummary(expired)
        BE-->>FE: expired summary
    end
```

---

## 4. 读图结论

这个登录链路不是普通的“前端表单直连远端 auth”，而是：

1. 前端只负责交互与显示  
2. 本地 FastAPI 充当 auth 代理与状态真相源  
3. AuthService 负责 session 编排、token 持久化、设备绑定、恢复与刷新  
4. 前端最终按本地 `auth_state` 来决定是否放行路由

