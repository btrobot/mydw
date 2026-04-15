# Release Governance Tabletop Record - Example

## Purpose

Provide the minimum tabletop proof artifact for **PR-A0.4**.

The record must show that operators can reason through:

1. a bad release rollback path
2. a restore-needed recovery path
3. release evidence checklist completion

## Record metadata

- Environment: `staging`
- Candidate identifier: `remote-full-system-v1-rc1`
- Operators: `example-operator`, `example-reviewer`
- Timestamp: `2026-04-15T00:00:00Z`

## Scenario 1 - Bad release rollback path

- Trigger: compatibility drift detected after candidate rollout
- Decision: block promotion and roll back to last known-good candidate
- Evidence checked:
  - rollback target identifier recorded
  - rollback runbook reviewed
  - post-rollback validation checklist completed
- Result: `pass` or `block`
- Notes: explain what blocked or succeeded

## Scenario 2 - Restore-needed recovery path

- Trigger: rollback alone does not recover authoritative database correctness
- Decision: restore from approved backup or snapshot
- Evidence checked:
  - backup ownership identified
  - restore source identifier recorded
  - restore verification expectations reviewed
  - post-restore validation completed
- Result: `pass` or `block`
- Notes: explain what blocked or succeeded

## Scenario 3 - Release evidence checklist completion

- Required bundle reviewed:
  - backend regression green
  - contract gates green
  - admin smoke evidence
  - deploy smoke evidence
  - portal smoke placeholder noted for Program B
  - promotion checklist reviewed
  - rollback runbook reviewed
  - restore runbook reviewed
- Result: `pass` or `block`
- Notes: explain what evidence is missing if blocked

## Rule

At least one tabletop record must exist before Complete System v1 leaves A0 and
enters broader productionization work.
