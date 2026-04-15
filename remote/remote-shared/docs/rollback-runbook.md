# Rollback Runbook

## Purpose

Provide the minimum rollback sequence for a failed remote release or staging
promotion.

## Trigger conditions

Rollback should be considered when:

- compatibility gate fails after deployment
- admin login shell cannot sign in
- dashboard/users/devices/sessions/audit core paths are broken
- bootstrap admin cannot be created or rotated
- a release introduces contract drift or unsafe operator behavior

## Rollback checklist

### 1. Freeze promotion

- stop additional rollout
- announce the candidate is blocked

### 2. Identify rollback target

- use the last known-good build / commit / deployment identifier
- confirm its compatibility gate evidence exists

### 3. Revert deployment

- restore previous backend artifact
- restore previous admin build
- restore previous environment binding if needed

### 4. Verify rollback

- `/admin/login` works
- dashboard loads
- users/devices/sessions/audit all load
- compatibility harness passes against the rolled-back environment

### 5. Record the rollback

Capture:

- rollback target
- who executed rollback
- when rollback completed
- suspected root cause

## Important note

Rollback assets must be reviewed before release promotion, not after failure.
