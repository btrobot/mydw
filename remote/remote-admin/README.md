# remote-admin

Protected admin console for the remote authorization center.

## Current scope

- admin login shell
- dashboard
- users / devices / sessions / audit pages
- role-aware destructive actions

## Local run

```bash
npm run typecheck
npm run build
npm run build:react
```

Default static entry (matches `scripts/start-remote.bat`):

```text
dist-react/index.html?apiBase=http://127.0.0.1:8100
```

Use `npm run dev` during development; the Vite dev server opens `/index.html`.

## Linux deployment

The Linux deployment baseline uses:

- `Dockerfile`
- `public/config.js`
- `scripts/render-runtime-config.sh`
- `../.env.linux.example`
- `../remote-shared/deploy/docker-compose.linux.yml`
- `../remote-shared/deploy/nginx.remote-full-system-https.conf.template`

At runtime the container writes `config.js` from
`REMOTE_ADMIN_API_BASE_URL`, so the deployed admin should normally point to
`/api` behind the reverse proxy.

## Real smoke entries

After `scripts/start-remote.bat` has started the backend and static server, run:

```bash
npm run smoke:users:create
npm run smoke:users:update
npm run smoke:users:update:multi
npm run smoke:users
```

These commands will rebuild `dist-react`, run the real browser smoke, and write
timestamped evidence into `discss/artifacts/`.

- `smoke:users:create`
  - creates a real user through the UI and verifies reload/search lookup
- `smoke:users:update`
  - covers create + direct update + sensitive update + revoke/restore + API verification
- `smoke:users:update:multi`
  - covers multi-user draft isolation, reset semantics, and real selected-user update flow
- `smoke:users`
  - builds once, then runs all three smokes in sequence
  - writes grouped evidence into `remote-users-smoke-suite-*/create`, `update`, `update-multi`
  - auto-waits across admin step-up rate-limit windows so the full suite stays stable end-to-end

You can override the artifact directory if needed:

```powershell
$env:REMOTE_SMOKE_ARTIFACT_DIR='E:\tmp\remote-users-smoke'
npm run smoke:users:create
npm run smoke:users:update
npm run smoke:users:update:multi
```

If your backend overrides the default admin step-up rate limit, you can pass the
same env vars into the suite runner:

```powershell
$env:REMOTE_BACKEND_ADMIN_STEP_UP_RATE_LIMIT_WINDOW_SECONDS='90'
$env:REMOTE_BACKEND_ADMIN_STEP_UP_RATE_LIMIT_MAX_ATTEMPTS='4'
npm run smoke:users
```

## Release gate

```bash
npm run typecheck
npm run build
npm run build:react
npm run test
npm run test:react-step-up
npm run smoke:users:create
npm run smoke:users:update
npm run smoke:users:update:multi
```

See `../remote-shared/docs/phase3-release-gate.md` for the full backend + compatibility + admin gate sequence.
