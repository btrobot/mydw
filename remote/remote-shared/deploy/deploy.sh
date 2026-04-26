#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/common.sh"

MODE=${1:-apply}

ensure_prerequisites
load_env_file
validate_server_env
render_nginx_conf
verify_compose_render

if [ "$MODE" = "--render-only" ]; then
  log "rendered nginx and compose config successfully"
  exit 0
fi

BEFORE_REF=$(current_git_ref)
run_compose_up
AFTER_REF=$(current_git_ref)
record_success_refs "$BEFORE_REF" "$AFTER_REF"
log "deployment applied"
