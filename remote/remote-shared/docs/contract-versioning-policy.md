# Contract Versioning Policy

## Current version

- Remote auth contract version: `v1`

## Source-of-truth order

The canonical order for Phase 0 artifacts is:

1. domain boundary docs
2. token/session model docs
3. error semantics / error-code matrix
4. OpenAPI contract artifact
5. DB schema draft

## Breaking changes

The following are breaking changes:

- adding a new required field
- removing an existing field
- changing error-code meaning
- changing token/session semantics
- changing device binding semantics
- changing `license_status` or `device_status` meaning

## Required follow-up for a breaking change

When a breaking change happens, the change must include:

- explicit version bump beyond `v1`
- OpenAPI update
- fixture update
- compatibility harness update
