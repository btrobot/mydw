#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/common.sh"

MODE=${1:-apply}

ensure_prerequisites
load_env_file
validate_server_env
ensure_clean_git_tree

BEFORE_REF=$(current_git_ref)
git -C "$REPO_ROOT" fetch origin "$REMOTE_DEPLOY_BRANCH"
git -C "$REPO_ROOT" checkout "$REMOTE_DEPLOY_BRANCH"
git -C "$REPO_ROOT" pull --ff-only origin "$REMOTE_DEPLOY_BRANCH"

render_nginx_conf
verify_compose_render

if [ "$MODE" = "--render-only" ]; then
  log "upgrade render-only check passed"
  exit 0
fi

run_compose_up
AFTER_REF=$(current_git_ref)
record_success_refs "$BEFORE_REF" "$AFTER_REF"
log "upgrade applied from $BEFORE_REF to $AFTER_REF"
