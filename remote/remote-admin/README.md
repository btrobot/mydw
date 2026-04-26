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

## Real smoke entry

After `scripts/start-remote.bat` has started the backend and static server, run:

```bash
npm run smoke:users:update:multi
```

This command will:

- rebuild `dist-react`
- run the real multi-user Users Update browser smoke
- write timestamped evidence into `discss/artifacts/remote-users-update-multi-smoke-*`

You can override the artifact directory if needed:

```powershell
$env:REMOTE_SMOKE_ARTIFACT_DIR='E:\tmp\remote-users-smoke'
npm run smoke:users:update:multi
```

## Release gate

```bash
npm run typecheck
npm run build
npm run build:react
npm run test
npm run test:react-step-up
npm run smoke:users:update:multi
```

See `../remote-shared/docs/phase3-release-gate.md` for the full backend + compatibility + admin gate sequence.
