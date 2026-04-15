# Restore Recovery Runbook

## Purpose

Provide the minimum restore and recovery baseline for a remote release when
rollback alone is insufficient or when the authoritative database state must be
recovered.

This document is part of the **PR-A0.4** release-governance baseline.

## Trigger conditions

Use this runbook when one or more of the following hold:

- rollback cannot restore service correctness by itself
- the authoritative database state is corrupt, missing, or inconsistent
- an operator must restore from a backup or snapshot
- post-release validation shows unrecoverable data drift

## Backup ownership baseline

- infrastructure or platform operators own backup scheduling and storage
- application operators own restore decision records and post-restore validation
- the release candidate record must identify the backup or snapshot source that
  would be used for recovery
- backup provenance must be known before promotion, not after failure

## Restore prerequisites

Before restore begins, record:

- candidate build / environment identifier
- restore trigger summary
- chosen backup or snapshot identifier
- restore operator
- expected rollback target, if one also exists

## Restore sequence

### 1. Freeze change activity

- stop additional rollout
- block follow-up migrations or admin write activity if needed

### 2. Select restore source

- choose the last known-good backup or snapshot
- confirm source timestamp and environment alignment

### 3. Restore data and runtime

- restore the authoritative database from the selected source
- redeploy or re-bind the last known-good backend/admin artifacts if needed
- confirm environment config still matches the approved release baseline

### 4. Restore verification expectations

The environment is not considered recovered until all of the following pass:

- backend `/health` returns `{"status": "ok"}`
- admin login works
- dashboard, users, devices, sessions, and audit core paths load
- compatibility gate or smoke checks pass against the recovered environment
- operator confirms the restored environment matches the intended candidate or
  rollback target state

## Post-rollback / post-restore validation checklist

Capture and confirm:

- current backend artifact identifier
- current admin artifact identifier
- restored backup or snapshot identifier
- compatibility result
- admin smoke result
- outstanding data-loss or drift notes
- next action: promote again, remain blocked, or escalate

## Record requirements

Every restore/recovery event must record:

- who initiated restore
- who approved restore
- when restore began and ended
- what backup/snapshot was used
- whether rollback also occurred
- what validation evidence was captured afterward

## Important note

If restore evidence is incomplete, treat the environment as **not release-ready**
even when the service appears healthy.
