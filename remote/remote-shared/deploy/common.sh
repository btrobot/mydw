#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)
REMOTE_ROOT="$REPO_ROOT/remote"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.linux.yml"
ENV_FILE="${REMOTE_DEPLOY_ENV_FILE:-$REPO_ROOT/.env}"
ENV_TEMPLATE="$REMOTE_ROOT/.env.linux.example"
STATE_DIR="$SCRIPT_DIR/.deploy-state"
GENERATED_NGINX_CONF="$SCRIPT_DIR/nginx.remote-full-system.generated.conf"
HTTP_NGINX_CONF="$SCRIPT_DIR/nginx.remote-full-system-linux.conf"
HTTPS_NGINX_TEMPLATE="$SCRIPT_DIR/nginx.remote-full-system-https.conf.template"
CERTS_DIR="$SCRIPT_DIR/certs"

log() {
  printf '[remote-deploy] %s\n' "$*"
}

fail() {
  printf '[remote-deploy][ERROR] %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "missing required command: $1"
}

ensure_prerequisites() {
  require_cmd docker
  require_cmd git
  require_cmd sed
  mkdir -p "$STATE_DIR"
}

ensure_env_file() {
  [ -f "$ENV_FILE" ] || fail "env file not found: $ENV_FILE (copy $ENV_TEMPLATE first)"
}

load_env_file() {
  ensure_env_file
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
}

placeholder_guard() {
  value=$1
  name=$2
  case "$value" in
    ""|"change-me-"*|"replace-with-"*|*example.com*)
      fail "$name still uses a placeholder value"
      ;;
  esac
}

validate_server_env() {
  : "${REMOTE_DEPLOY_TLS_MODE:=http}"
  : "${REMOTE_DEPLOY_BRANCH:=main}"

  [ "${REMOTE_BACKEND_APP_ENV:-}" = "staging" ] || [ "${REMOTE_BACKEND_APP_ENV:-}" = "prod" ] || \
    fail "REMOTE_BACKEND_APP_ENV must be staging or prod for Linux deployment"

  placeholder_guard "${REMOTE_BACKEND_ADMIN_BOOTSTRAP_PASSWORD:-}" "REMOTE_BACKEND_ADMIN_BOOTSTRAP_PASSWORD"
  placeholder_guard "${REMOTE_COMPAT_ADMIN_PASSWORD:-}" "REMOTE_COMPAT_ADMIN_PASSWORD"

  case "$REMOTE_DEPLOY_TLS_MODE" in
    http) ;;
    https)
      placeholder_guard "${REMOTE_DEPLOY_SERVER_NAME:-}" "REMOTE_DEPLOY_SERVER_NAME"
      [ -f "$CERTS_DIR/fullchain.pem" ] || fail "missing TLS cert: $CERTS_DIR/fullchain.pem"
      [ -f "$CERTS_DIR/privkey.pem" ] || fail "missing TLS key: $CERTS_DIR/privkey.pem"
      ;;
    *)
      fail "REMOTE_DEPLOY_TLS_MODE must be http or https"
      ;;
  esac
}

render_nginx_conf() {
  case "${REMOTE_DEPLOY_TLS_MODE:-http}" in
    http)
      cp "$HTTP_NGINX_CONF" "$GENERATED_NGINX_CONF"
      ;;
    https)
      sed "s/__REMOTE_SERVER_NAME__/${REMOTE_DEPLOY_SERVER_NAME}/g" \
        "$HTTPS_NGINX_TEMPLATE" > "$GENERATED_NGINX_CONF"
      ;;
  esac
}

compose_cmd() {
  docker compose -f "$COMPOSE_FILE" "$@"
}

verify_compose_render() {
  compose_cmd config >/dev/null
}

current_git_ref() {
  git -C "$REPO_ROOT" rev-parse HEAD
}

ensure_clean_git_tree() {
  if ! git -C "$REPO_ROOT" diff --quiet || ! git -C "$REPO_ROOT" diff --cached --quiet; then
    fail "git worktree is dirty; commit or stash local changes before deploy automation"
  fi
}

record_success_refs() {
  before_ref=${1:-}
  after_ref=${2:-}
  if [ -n "$before_ref" ] && [ -n "$after_ref" ] && [ "$before_ref" != "$after_ref" ]; then
    printf '%s\n' "$before_ref" > "$STATE_DIR/previous-successful-ref"
  fi
  if [ -n "$after_ref" ]; then
    printf '%s\n' "$after_ref" > "$STATE_DIR/last-successful-ref"
  fi
}

run_compose_up() {
  compose_cmd up -d --build
}
