# remote-backend

FastAPI backend for the remote authorization center and admin control plane.

## Responsibilities

- public auth APIs: `/login`, `/refresh`, `/logout`, `/me`
- admin auth + control APIs
- user / device / session / license truth
- audit, tracing, and metrics

## Local run

From `remote/remote-backend/`:

```bash
python -c "from app.migrations.runner import upgrade; upgrade()"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
```

## Bootstrap the first admin

```bash
set BOOTSTRAP_ADMIN_PASSWORD=admin-secret
python scripts/bootstrap_admin.py --migrate --username admin --password-env BOOTSTRAP_ADMIN_PASSWORD --role super_admin --display-name "Remote Admin"
```

The script is idempotent: rerunning it updates the matching admin account.

## Recommended staging env

At minimum configure:

- `REMOTE_BACKEND_APP_ENV`
- `REMOTE_BACKEND_HOST`
- `REMOTE_BACKEND_PORT`
- `REMOTE_BACKEND_DATABASE_URL`
- `REMOTE_BACKEND_CORS_ALLOW_ORIGINS`
- `REMOTE_BACKEND_ADMIN_BOOTSTRAP_USERNAME`
- `REMOTE_BACKEND_ADMIN_BOOTSTRAP_PASSWORD`

Use non-default bootstrap secrets in staging and production. `ensure_seed_admin()`
only runs in `development` and `test`; staging/prod should rely on the bootstrap script.

See:

- `../.env.example`
- `../remote-shared/docs/admin-bootstrap-runbook.md`
- `../remote-shared/docs/staging-deploy-checklist.md`
