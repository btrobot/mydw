#!/bin/sh
set -eu

cat > /usr/share/nginx/html/config.js <<EOF
window.REMOTE_ADMIN_RUNTIME_CONFIG = {
  apiBase: "${REMOTE_ADMIN_API_BASE_URL:-/api}"
};
EOF
