#!/bin/bash
# session-end.sh: Session cleanup hook
# 会话结束钩子

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SESSION_STATE="$PROJECT_ROOT/production/session-state/active.md"

GREEN='\033[0;32m'
NC='\033[0m'

log_success() {
    echo -e "${GREEN}[OK]${NC} $*"
}

# 检查未保存的更改
check_unsaved() {
    if command -v git &> /dev/null && git rev-parse --is-inside-work-tree &> /dev/null; then
        if ! git diff --quiet 2>/dev/null; then
            echo ""
            echo "[WARN] 有未提交的更改:"
            git status --short
            echo ""
        fi
    fi
}

# 更新会话状态
update_session_state() {
    if [ -f "$SESSION_STATE" ]; then
        # 添加会话结束时间
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        if grep -q "## 会话历史" "$SESSION_STATE"; then
            # 追加到历史
            sed -i "s/## 会话历史/## 会话历史\n\n### $timestamp\n- 会话结束/" "$SESSION_STATE"
        fi
    fi
}

# 显示下一步建议
show_next_steps() {
    echo ""
    echo "========================================"
    echo "  会话结束建议"
    echo "========================================"
    echo ""
    echo "  1. 确认所有更改已提交"
    echo "  2. 运行 /code-review 审查代码"
    echo "  3. 运行 /security-scan 检查安全"
    echo "  4. 更新 session-state 记录"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "========================================"
    echo "  得物掘金工具 - 会话结束"
    echo "========================================"

    check_unsaved
    update_session_state
    show_next_steps

    log_success "会话清理完成"
    exit 0
}

main "$@"
