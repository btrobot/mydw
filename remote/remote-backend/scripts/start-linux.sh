#!/bin/sh
set -eu

python scripts/migrate.py ensure-head

exec python -m uvicorn app.main:app \
  --host "${REMOTE_BACKEND_HOST:-0.0.0.0}" \
  --port "${REMOTE_BACKEND_PORT:-8100}"
