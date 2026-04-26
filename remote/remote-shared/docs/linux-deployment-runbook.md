# Linux Deployment Runbook

## Purpose

Provide a repeatable Linux deployment baseline for `remote-backend`,
`remote-admin`, and the shared reverse proxy.

## Deployment assets

- `../../.env.linux.example`
- `../deploy/docker-compose.linux.yml`
- `../deploy/nginx.remote-full-system-linux.conf`
- `../deploy/nginx.remote-full-system-https.conf.template`
- `../deploy/remote-compose.service`
- `../deploy/deploy.sh`
- `../deploy/upgrade.sh`
- `../deploy/rollback.sh`
- `../../remote-backend/Dockerfile`
- `../../remote-admin/Dockerfile`

## 1. Prerequisites

- Linux host with Docker Engine and Docker Compose plugin
- repo checked out on the target host
- root or sudo access for binding port 80 and installing systemd units

## 2. Prepare env

Copy `remote/.env.linux.example` to repo-root `.env`, then override at least:

- `REMOTE_DEPLOY_BRANCH`
- `REMOTE_DEPLOY_TLS_MODE`
- `REMOTE_DEPLOY_SERVER_NAME`
- `REMOTE_BACKEND_APP_ENV=staging`
- `REMOTE_BACKEND_HOST=0.0.0.0`
- `REMOTE_BACKEND_PORT=8100`
- `REMOTE_BACKEND_DATABASE_URL`
- `REMOTE_BACKEND_CORS_ALLOW_ORIGINS`
- `REMOTE_BACKEND_ADMIN_BOOTSTRAP_USERNAME`
- `REMOTE_BACKEND_ADMIN_BOOTSTRAP_PASSWORD`
- `REMOTE_ADMIN_API_BASE_URL=/api`

Recommended SQLite baseline on a single host:

```env
REMOTE_BACKEND_DATABASE_URL=sqlite:////data/remote_auth.db
REMOTE_BACKEND_LOGIN_RATE_LIMIT_SQLITE_PATH=/data/login_rate_limits.sqlite3
```

If you want HTTPS, set:

```env
REMOTE_DEPLOY_TLS_MODE=https
REMOTE_DEPLOY_SERVER_NAME=remote.example.com
```

Then place the certificate files here before deployment:

- `remote/remote-shared/deploy/certs/fullchain.pem`
- `remote/remote-shared/deploy/certs/privkey.pem`

If you run `docker compose -f remote/remote-shared/deploy/docker-compose.linux.yml ...`
directly without a repo-root `.env`, Compose now falls back to
`remote/.env.linux.example` for container env injection. That avoids the
missing-file hard failure, but you should still create a real repo-root `.env`
before any non-local staging/prod deployment so placeholder secrets and example
hostnames are not used.

## 3. Build and start

From the repository root:

```bash
remote/remote-shared/deploy/deploy.sh
```

The backend container auto-runs `python scripts/migrate.py ensure-head` before
starting uvicorn.

For a config-only verification without starting containers:

```bash
remote/remote-shared/deploy/deploy.sh --render-only
```

## 4. Bootstrap the first admin

```bash
export BOOTSTRAP_ADMIN_PASSWORD='change-me-now'
docker compose -f remote/remote-shared/deploy/docker-compose.linux.yml exec \
  remote-backend \
  python scripts/bootstrap_admin.py \
  --username staging-admin \
  --password-env BOOTSTRAP_ADMIN_PASSWORD \
  --role super_admin \
  --display-name "Staging Admin"
```

## 5. Verify

```bash
curl http://127.0.0.1/health
docker compose -f remote/remote-shared/deploy/docker-compose.linux.yml ps
docker compose -f remote/remote-shared/deploy/docker-compose.linux.yml logs remote-backend --tail 100
```

Expected outcomes:

- `/health` returns `{"status":"ok"}`
- `/admin/` opens the built admin console
- admin frontend calls the backend through `/api`

## 6. Upgrade

```bash
remote/remote-shared/deploy/upgrade.sh
```

This script:

- fetches `origin/$REMOTE_DEPLOY_BRANCH`
- fast-forwards the server checkout
- re-renders the active nginx config
- rebuilds and restarts the compose services

## 7. Rollback

Rollback to the previously recorded successful ref:

```bash
remote/remote-shared/deploy/rollback.sh
```

Or rollback to an explicit tag / commit:

```bash
remote/remote-shared/deploy/rollback.sh <git-ref>
```

The rollback checkout is detached on purpose. A later `upgrade.sh` will switch
back to `REMOTE_DEPLOY_BRANCH` before pulling the next candidate.

## 8. Optional systemd registration

Adjust `../deploy/remote-compose.service` if the checkout path is not
`/opt/mydw`, then install it:

```bash
sudo cp remote/remote-shared/deploy/remote-compose.service /etc/systemd/system/remote-compose.service
sudo systemctl daemon-reload
sudo systemctl enable --now remote-compose.service
```

## 9. Related docs

- `staging-deploy-checklist.md`
- `rollback-runbook.md`
- `restore-recovery-runbook.md`
