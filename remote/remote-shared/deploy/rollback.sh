#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck disable=SC1091
. "$SCRIPT_DIR/common.sh"

ensure_prerequisites
load_env_file
validate_server_env
ensure_clean_git_tree

TARGET_REF=${1:-}
if [ -z "$TARGET_REF" ]; then
  [ -f "$STATE_DIR/previous-successful-ref" ] || fail "no previous-successful-ref recorded; pass a target ref explicitly"
  TARGET_REF=$(cat "$STATE_DIR/previous-successful-ref")
fi

CURRENT_REF=$(current_git_ref)
git -C "$REPO_ROOT" fetch --all --tags --prune
git -C "$REPO_ROOT" checkout --detach "$TARGET_REF"

render_nginx_conf
verify_compose_render
run_compose_up

ROLLED_BACK_REF=$(current_git_ref)
record_success_refs "$CURRENT_REF" "$ROLLED_BACK_REF"
log "rollback applied to $ROLLED_BACK_REF"
