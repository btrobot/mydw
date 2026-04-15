# Admin Bootstrap Runbook

## Purpose

Create or rotate the first admin account for a new remote deployment without editing database rows by hand.

## Inputs

- backend database is reachable
- backend env is configured
- operator knows the desired username / password / role

## Script

Use one of the safe password input modes:

```bash
set BOOTSTRAP_ADMIN_PASSWORD=admin-secret
python remote/remote-backend/scripts/bootstrap_admin.py --migrate --username admin --password-env BOOTSTRAP_ADMIN_PASSWORD --role super_admin --display-name "Remote Admin"
```

The script will:

1. optionally run backend migrations
2. create the admin if it does not exist
3. update password / role / display name / status if it already exists

It prints JSON with `created` or `updated`.

## Development

Recommended:

```bash
set BOOTSTRAP_ADMIN_PASSWORD=admin-secret
python remote/remote-backend/scripts/bootstrap_admin.py --migrate --username admin --password-env BOOTSTRAP_ADMIN_PASSWORD --role super_admin --display-name "Remote Admin"
```

Defaults are intentionally simple for local use only.

## Staging

Recommended:

```bash
set REMOTE_BACKEND_APP_ENV=staging
set REMOTE_BACKEND_ADMIN_BOOTSTRAP_USERNAME=unused-in-staging
set REMOTE_BACKEND_ADMIN_BOOTSTRAP_PASSWORD=unused-in-staging
set STAGING_BOOTSTRAP_PASSWORD=change-me-now
python remote/remote-backend/scripts/bootstrap_admin.py --migrate --username staging-admin --password-env STAGING_BOOTSTRAP_PASSWORD --role super_admin --display-name "Staging Admin"
```

After bootstrap:

1. sign in through `/admin/login`
2. open the remote admin console
3. verify dashboard / users / devices / sessions / audit
4. rotate the staging password if it was shared during setup

Hard requirement:

- staging must not keep development bootstrap secrets
- staging must not rely on automatic development seeding behavior
- set `REMOTE_BACKEND_APP_ENV=staging` before startup so runtime seeding stays off

## Production note

Do not commit production credentials.

For production:

- inject secrets through the deployment platform
- run the bootstrap script in a one-shot admin job
- store the password in the organization-approved secret manager
- prefer `--password-env` or `--password-stdin`; avoid command-line passwords

## Recovery

If the seeded admin password is lost:

1. run the same script again with the same username
2. set a new password
3. verify sign-in
4. record the rotation in the operator log
