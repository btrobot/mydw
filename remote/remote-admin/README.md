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

Recommended static entry (matches `scripts/start-remote.bat`):

```text
dist-react/react-index.html?apiBase=http://127.0.0.1:8100
```

Legacy fallback remains available at:

```text
index.html?apiBase=http://127.0.0.1:8100
```

Use `npm run dev` during React-shell development; the Vite dev server opens `/react-index.html`.

## Release gate

```bash
npm run typecheck
npm run build
npm run build:react
npm run test
npm run test:react-step-up
```

See `../remote-shared/docs/phase3-release-gate.md` for the full backend + compatibility + admin gate sequence.
