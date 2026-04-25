# Staging Deploy Checklist

## Purpose

Provide the minimum repeatable checklist to bring up the remote backend and admin console in a staging-like environment.

## 1. Prepare env

Start from `remote/.env.example` and set at least:

- `REMOTE_STAGING_PUBLIC_BASE_URL`
- `REMOTE_STAGING_ADMIN_BASE_URL`
- `REMOTE_BACKEND_APP_ENV`
- `REMOTE_BACKEND_HOST`
- `REMOTE_BACKEND_PORT`
- `REMOTE_BACKEND_DATABASE_URL`
- `REMOTE_BACKEND_CORS_ALLOW_ORIGINS`
- `REMOTE_BACKEND_ADMIN_BOOTSTRAP_USERNAME`
- `REMOTE_BACKEND_ADMIN_BOOTSTRAP_PASSWORD`
- `REMOTE_COMPAT_BASE_URL`
- `REMOTE_COMPAT_ADMIN_USERNAME`
- `REMOTE_COMPAT_ADMIN_PASSWORD`

Hard requirements:

- override all development/bootstrap defaults from `.env.example`
- use unique staging-only admin/bootstrap secrets
- set `REMOTE_BACKEND_APP_ENV=staging`
- do not leave development seed credentials enabled in staging

## 2. Start backend

From `remote/remote-backend/`:

```bash
python scripts/migrate.py ensure-head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8100
```

## 3. Bootstrap the first admin

```bash
set STAGING_BOOTSTRAP_PASSWORD=change-me-now
python remote/remote-backend/scripts/bootstrap_admin.py --migrate --username staging-admin --password-env STAGING_BOOTSTRAP_PASSWORD --role super_admin --display-name "Staging Admin"
```

## 4. Build the admin console

```bash
npm --prefix remote/remote-admin run build
```

Serve or open:

```text
remote/remote-admin/index.html?apiBase=https://remote-staging.example.com
```

## 5. Run staging compatibility smoke

```bash
REMOTE_COMPAT_BASE_URL=https://remote-staging.example.com \
REMOTE_COMPAT_ADMIN_USERNAME=staging-admin \
REMOTE_COMPAT_ADMIN_PASSWORD=change-me-now \
python remote/remote-shared/scripts/compat-harness/validate_phase1_gate.py
```

## 6. Manual admin smoke

Verify:

- admin login works
- dashboard renders metrics
- users list/detail works
- devices list/detail works
- sessions list/detail works
- audit log page renders
- one safe destructive action is visible and audited in staging

## 7. Release-gate evidence

Capture:

- backend regression output
- compatibility gate output
- remote-admin typecheck/build/test output
- bootstrap script JSON output

## Failure policy

If any step fails:

- do not mark staging ready
- fix env/runtime drift first
- rerun bootstrap only if admin credentials are the problem
