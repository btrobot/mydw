
  你们的需求（设备授权 + 离线 grace mode + license 检查）决定了必须走范式 B，范式 A 满足不了。

  ---
  具体的减重建议

  建议 1：合并两个存储为一个

  # 现在：状态在 DB，token 在加密文件，需要协调
  RemoteAuthSession(DB) + secret_store(file)

  # 改成：一个加密的本地 JSON 文件，全量存
  {
    "auth_state": "authenticated_active",
    "access_token": "...",      # 加密
    "refresh_token": "...",     # 加密
    "expires_at": "...",
    "user_info": {...},
    "device_id": "...",
    "offline_grace_until": "..."
  }

  好处：原子读写，无协调问题，启动时一次读完，不需要 DB 表。
  实现：现有的 secret_store.py 的 AES-256-GCM 机制可以复用，只是扩展存储内容。

  建议 2：设备身份单一来源

  Electron Main Process 启动时生成/读取 device_id
    → 存在 app.getPath('userData') 下的文件（OS 保护的目录）
    → 通过 IPC 传给 Renderer（前端不自己生成）
    → 本地后端从同一目录读取（或通过 IPC 获取）

  localStorage 的那份可以删掉——桌面应用不需要用浏览器机制存设备身份。

  建议 3：状态从 9 个压缩到 4 个

  # 用户视角实际只有 4 种情况：
  ACTIVE   = "active"    # 正常使用
  GRACE    = "grace"     # 离线宽限，只读
  EXPIRED  = "expired"   # 需要重新登录
  REVOKED  = "revoked"   # 被吊销，无法登录

  # 现有的细粒度状态（authorizing/refresh_required/device_mismatch/error）
  # 都是内部过渡状态，不应该暴露给 UI 路由

  前端路由判断从 9 个分支简化到 4 个。内部过渡状态在 service 层处理掉，不写入持久化存储。

  建议 4：前端只保留一条 session 同步路径

  // 删掉 axios interceptor 里的 syncSession()
  // 只保留：
  // 1. 启动时 fetch（一次）
  // 2. 用户主动操作（refresh、logout）触发更新

  // 401/403 的处理：直接跳转登录页，不做中间 syncSession

  大多数 401/403 是 session 已经失效，再 sync 一次得到的还是失效状态，多一个 round-trip 没有意义。

  ---
  改后的架构示意

  启动
    ↓
  读取本地加密 session 文件（一次 IO）
    ↓
  状态判断（4 个分支）
    ├── active   → 正常进入，Header 带 access_token
    ├── grace    → 进入只读模式，后台尝试 refresh
    ├── expired  → 跳登录页
    └── revoked  → 跳吊销页（不可恢复）

  每次 API 请求
    ↓
  检查内存中的 session（不读 DB，不读文件）
    ├── active → 放行
    └── 其他  → 401 → 前端跳登录页

  Token 刷新（独立触发，不阻塞请求）
    ↓
  调远端 refresh
    ↓
  原子写回本地加密文件
    ↓
  更新内存 session

  这样改完，auth_dependencies.py 里的 DB 查询可以换成内存读取，secret_store 和 RemoteAuthSession 表合并为一个模块，前端路由分支从 9
   个变 4 个。整体代码量估计能减少 30-40%，同时逻辑更清晰。
   