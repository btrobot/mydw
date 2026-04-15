# Schema Freeze vs Migration Generation Policy

## Purpose

Clarify what is frozen in Phase 0 and what remains deferred to implementation.

## Phase 0

Phase 0 freezes:

- DB schema draft
- table responsibilities
- key relationships
- index recommendations

Phase 0 does not generate final business migrations.

## Phase 1

Phase 1 is where:

- real migrations are created
- migration ordering is implemented
- runtime persistence is introduced

## Freeze rule

Schema draft changes are allowed only through review during Phase 0.
Business migrations are implementation artifacts and must not redefine the frozen model silently.
