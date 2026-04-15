# Remote Shared Artifacts

This directory is **artifact-only**.

## Allowed

- OpenAPI artifacts
- generated clients / generated types
- documentation
- utility scripts

## Forbidden

- runtime service logic
- token issuance logic
- permission decision logic
- shared domain services imported by live apps

Phase 0 freezes this boundary so later implementation work cannot blur auth-core and admin-console responsibilities.
