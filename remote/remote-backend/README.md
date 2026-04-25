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
python scripts/migrate.py ensure-head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8100
```

## Database migrations

Day 5.2 promotes Alembic to the default local/test migration entrypoint while the legacy
runner stays in the repo only as a temporary compatibility artifact.

For a brand-new empty database, from `remote/remote-backend/`:

```bash
python scripts/migrate.py upgrade head
python scripts/migrate.py current
python scripts/migrate.py downgrade base
```

If your local database predates Alembic, stamp it first instead of
rerunning the baseline DDL:

```bash
python scripts/migrate.py stamp 20260425_0001
python scripts/migrate.py upgrade head
python scripts/migrate.py current
```

`python scripts/migrate.py ensure-head` is the safest default for local setup: it upgrades
empty databases, and it adopts pre-Alembic databases by stamping the baseline before
moving to `head`.

## Schema change workflow

Alembic is now the only supported schema evolution path.

- create a new revision from `remote/remote-backend/`
- put the schema change in `migrations/versions/`
- apply it with `python scripts/migrate.py upgrade head`

Example:

```bash
alembic revision -m "describe schema change"
python scripts/migrate.py upgrade head
```

Do not add or update schema through removed runner code or hand-maintained
`schema_migrations` state.

## Bootstrap the first admin

```bash
set BOOTSTRAP_ADMIN_PASSWORD=admin-secret
python scripts/bootstrap_admin.py --migrate --username admin --password-env BOOTSTRAP_ADMIN_PASSWORD --role super_admin --display-name "Remote Admin"
```

`--migrate` now uses the Alembic entrypoint above. The script remains idempotent:
rerunning it updates the matching admin account.

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
