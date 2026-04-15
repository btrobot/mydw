# Staging Promotion Checklist

## Purpose

Provide a deterministic checklist for deciding whether a staging deployment is
ready to promote toward release.

## Preconditions

- staging backend is reachable
- staging admin console points to the correct backend base URL
- bootstrap admin has been created or rotated safely
- compatibility harness credentials are set

## Checklist

### 1. Environment confirmation

- confirm `REMOTE_BACKEND_APP_ENV=staging`
- confirm non-default bootstrap/admin secrets are in use
- confirm development auto-seeding is disabled

### 2. Runtime smoke

- sign in via `/admin/login`
- load dashboard
- load users
- load devices
- load sessions
- load audit logs

### 3. Compatibility smoke

- run `validate_phase1_gate.py` against staging
- confirm PASS

### 4. Control-plane smoke

- inspect at least one user detail
- inspect at least one device detail
- inspect at least one session detail
- confirm audit query works with filters

### 5. Risk review

- verify no default credentials remain
- verify current rollback notes are still valid
- verify support operator escalation path is still accurate

### 6. Sign-off

Record:

- environment name / URL
- operator name
- timestamp
- result: pass or block
- blocker summary if failed

## Promotion rule

Do not promote if any checklist item is incomplete or ambiguous.
