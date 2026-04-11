#!/usr/bin/env bash
set -euo pipefail

BACKEND_ROOT="${1:-${BACKEND_ROOT:-}}"
BACKEND_HOST="${2:-${BACKEND_HOST:-127.0.0.1}}"
BACKEND_PORT="${3:-${BACKEND_PORT:-8000}}"

if [[ -z "${BACKEND_ROOT}" ]]; then
  echo "BACKEND_ROOT is required" >&2
  exit 1
fi

PYTHON_BIN="${BACKEND_ROOT}/.venv/bin/python3"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="${BACKEND_ROOT}/venv/bin/python3"
fi
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

cd "${BACKEND_ROOT}"
exec "${PYTHON_BIN}" -m uvicorn main:app --port "${BACKEND_PORT}" --host "${BACKEND_HOST}"
