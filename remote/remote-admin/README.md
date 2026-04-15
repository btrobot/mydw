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
```

Then open:

```text
index.html?apiBase=http://127.0.0.1:8100
```

The `dev` script prints the same usage hint because this MVP console is a static TypeScript build without a separate app server.

## Release gate

```bash
npm run typecheck
npm run build
npm run test
```

See `../remote-shared/docs/phase3-release-gate.md` for the full backend + compatibility + admin gate sequence.
