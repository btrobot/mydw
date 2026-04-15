# remote-backend

Phase 0 bootstrap skeleton for the remote authorization center backend.

This app will own:

- public auth APIs (`/login`, `/refresh`, `/logout`, `/me`)
- admin APIs
- token/session/device/license truth
- audit, tracing, and metrics

Phase 0 intentionally avoids real auth runtime implementation.
