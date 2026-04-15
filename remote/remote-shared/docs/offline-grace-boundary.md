# Offline Grace Boundary

## Purpose

Freeze the line between what the remote system returns and what the local client decides.

## Remote responsibility

The remote system returns:

- policy
- truth
- grace-related fields
- version / license / device decisions

Examples:

- `offline_grace_until`
- `minimum_supported_version`
- `license_status`
- `device_status`

## Local responsibility

The local client remains responsible for:

- machine-session projection
- entering/exiting grace mode at runtime
- restricting local actions during grace
- mapping remote truth into local runtime states

## Freeze rule

The remote system must not attempt to fully control the local runtime grace state machine.
