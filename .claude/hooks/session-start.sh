#!/bin/bash
# session-start.sh: Session initialization hook
#
# Input: None
# Output: Project-specific session setup
# Exit codes: 0=success, 1=warning, 2=error

set -euo pipefail

# ============================================
# Configuration
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ============================================
# Functions
# ============================================

log_info() {
    echo "[INFO] $*"
}

log_warn() {
    echo "[WARN] $*" >&2
}

log_error() {
    echo "[ERROR] $*" >&2
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Node.js
    if command -v node &> /dev/null; then
        log_info "Node.js: $(node --version)"
    else
        log_warn "Node.js not found"
    fi

    # Check Python
    if command -v python &> /dev/null; then
        log_info "Python: $(python --version)"
    else
        log_warn "Python not found"
    fi

    # Check FFmpeg
    if command -v ffmpeg &> /dev/null; then
        log_info "FFmpeg: available"
    else
        log_warn "FFmpeg not found - AI clip features will be unavailable"
    fi

    # Check Playwright
    if [ -d "$PROJECT_ROOT/backend/venv" ]; then
        log_info "Python venv: configured"
    else
        log_warn "Python venv not found"
    fi
}

# ============================================
# Main Logic
# ============================================

main() {
    log_info "得物掘金工具 Session Started"
    log_info "Project root: $PROJECT_ROOT"

    check_prerequisites

    log_info "Available agents:"
    for agent in "$PROJECT_ROOT"/.claude/agents/*.md; do
        if [ -f "$agent" ]; then
            agent_name=$(basename "$agent" .md)
            echo "  - $agent_name"
        fi
    done

    log_info "Available skills:"
    for skill in "$PROJECT_ROOT"/.claude/skills/*/SKILL.md; do
        if [ -f "$skill" ]; then
            skill_name=$(basename "$(dirname "$skill")")
            echo "  - $skill_name"
        fi
    done

    exit 0
}

# ============================================
# Entry Point
# ============================================

main "$@"
