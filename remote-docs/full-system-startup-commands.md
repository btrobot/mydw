# 整个系统启动命令

> 适用目录：`E:\ais\mydw`
> Shell：PowerShell

---

## 1. 启动本地主系统

### 方式 A：推荐，一键启动

```powershell
cd E:\ais\mydw
.\dev.bat
```

### 方式 B：新的 3 脚本入口

```powershell
cd E:\ais\mydw
.\scripts\start-backend.bat
.\scripts\start-frontend.bat
.\scripts\start-remote.bat
```

说明：

- `scripts\start-backend.bat`
  - 只启动本地 `backend`
- `scripts\start-frontend.bat`
  - 一键启动本地前端
  - 若 `backend:8000` 未启动，会自动先拉起本地后端
- `scripts\start-remote.bat`
  - 一键启动 `remote-backend + remote-admin`
  - 会先构建 `remote-admin`，再 bootstrap admin 账号

---

### 方式 B：手工分开启动

#### 终端 1：本地后端

```powershell
cd E:\ais\mydw\backend
.\run.bat
```

#### 终端 2：本地前端

```powershell
cd E:\ais\mydw\frontend
npm run dev
```

---

## 2. 启动 remote-backend

### 终端 3：远端授权中心后端

```powershell
cd E:\ais\mydw\remote\remote-backend
python -c "from app.migrations.runner import upgrade; upgrade()"
$env:BOOTSTRAP_ADMIN_PASSWORD = "admin-secret"
python scripts/bootstrap_admin.py --migrate --username admin --password-env BOOTSTRAP_ADMIN_PASSWORD --role super_admin --display-name "Remote Admin"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
```

启动后访问：

```text
http://127.0.0.1:8100
```

---

## 3. 启动 remote-admin

### 终端 4：构建远端管理后台前端

```powershell
cd E:\ais\mydw
npm --prefix remote\remote-admin run build
```

然后直接打开：

```text
E:\ais\mydw\remote\remote-admin\index.html?apiBase=http://127.0.0.1:8100
```

---

## 4. 常用联调顺序

建议按下面顺序启动：

1. 本地主系统后端 / 前端
2. remote-backend
3. remote-admin

即：

```powershell
cd E:\ais\mydw
.\dev.bat
```

另开终端：

```powershell
cd E:\ais\mydw\remote\remote-backend
python -c "from app.migrations.runner import upgrade; upgrade()"
$env:BOOTSTRAP_ADMIN_PASSWORD = "admin-secret"
python scripts/bootstrap_admin.py --migrate --username admin --password-env BOOTSTRAP_ADMIN_PASSWORD --role super_admin --display-name "Remote Admin"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
```

再开终端：

```powershell
cd E:\ais\mydw
npm --prefix remote\remote-admin run build
```

然后打开：

```text
E:\ais\mydw\remote\remote-admin\index.html?apiBase=http://127.0.0.1:8100
```

---

## 5. 可选：启动前依赖安装命令

### 本地主系统依赖

```powershell
cd E:\ais\mydw\frontend
npm install

cd E:\ais\mydw\backend
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
python -m patchright install chromium
```

### remote-admin / remote-backend 依赖

```powershell
cd E:\ais\mydw\frontend
npm install

cd E:\ais\mydw\remote\remote-backend
python -m pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings pyyaml pytest httpx
```

---

## 6. 可选：一键验证命令

```powershell
cd E:\ais\mydw
pytest backend/tests/test_remote_phase0_bootstrap.py backend/tests/test_remote_phase0_contract_freeze.py backend/tests/test_remote_phase0_compatibility_gate.py backend/tests/test_remote_phase1_pr1_login.py backend/tests/test_remote_phase1_pr2_lifecycle.py backend/tests/test_remote_phase1_pr3_admin.py backend/tests/test_remote_phase1_pr4_gate.py backend/tests/test_remote_phase2_pr1_control_backbone.py backend/tests/test_remote_phase2_pr2_admin_users.py backend/tests/test_remote_phase2_pr3_admin_devices.py backend/tests/test_remote_phase2_pr4_admin_sessions.py backend/tests/test_remote_phase2_pr5_supportability.py backend/tests/test_remote_phase2_pr5_gate.py backend/tests/test_remote_phase3_pr1_admin_rbac.py backend/tests/test_remote_phase3_pr2_dashboard_audit.py backend/tests/test_remote_phase3_pr3_operations_ux.py backend/tests/test_remote_phase3_pr4_gate.py backend/tests/test_remote_phase4_pr1_contract_hardening.py backend/tests/test_remote_phase4_pr2_runtime_reliability.py backend/tests/test_remote_phase4_pr4_gate.py -q
python remote/remote-shared/scripts/compat-harness/export_phase1_openapi.py
python remote/remote-shared/scripts/compat-harness/build_phase1_manifest.py
python remote/remote-shared/scripts/compat-harness/build_phase0_manifest.py
python remote/remote-shared/scripts/compat-harness/validate_phase0_gate.py
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
npm --prefix remote/remote-admin run typecheck
npm --prefix remote/remote-admin run build
npm --prefix remote/remote-admin run test
```
