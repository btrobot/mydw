#!/usr/bin/env bash
set -euo pipefail

BACKEND_ROOT="${1:-${BACKEND_ROOT:-}}"

if [[ -z "${BACKEND_ROOT}" ]]; then
  echo "BACKEND_ROOT is required" >&2
  exit 1
fi

cd "${BACKEND_ROOT}"
exec "${BACKEND_ROOT}/backend"
