#!/bin/bash
# session-start.sh: Session initialization hook
# 得物掘金工具 - 会话开始钩子

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SESSION_STATE="$PROJECT_ROOT/production/session-state/active.md"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $*"
}

# 检查项目状态
check_project() {
    log_info "检查项目状态..."

    # 检查目录结构
    if [ -d "$PROJECT_ROOT/frontend" ] && [ -d "$PROJECT_ROOT/backend" ]; then
        log_success "项目结构完整"
    else
        log_warn "项目结构不完整"
    fi
}

# 检查开发环境
check_prerequisites() {
    log_info "检查开发环境..."

    # Node.js
    if command -v node &> /dev/null; then
        log_success "Node.js: $(node --version)"
    else
        log_warn "Node.js 未安装"
    fi

    # Python
    if command -v python &> /dev/null; then
        log_success "Python: $(python --version)"
    else
        log_warn "Python 未安装"
    fi

    # FFmpeg
    if command -v ffmpeg &> /dev/null; then
        log_success "FFmpeg: 可用"
    else
        log_warn "FFmpeg 未安装 - AI剪辑功能不可用"
    fi
}

# 加载会话状态
load_session_state() {
    if [ -f "$SESSION_STATE" ]; then
        log_info "加载会话状态..."

        # 提取当前状态
        CURRENT_TASK=$(grep -A 1 "Task:" "$SESSION_STATE" 2>/dev/null | tail -1 | sed 's/^[[:space:]]*//')
        CURRENT_EPIC=$(grep -A 1 "Epic:" "$SESSION_STATE" 2>/dev/null | tail -1 | sed 's/^[[:space:]]*//')
        CURRENT_FEATURE=$(grep -A 1 "Feature:" "$SESSION_STATE" 2>/dev/null | tail -1 | sed 's/^[[:space:]]*//')

        if [ -n "$CURRENT_TASK" ]; then
            echo ""
            echo -e "${GREEN}========================================"
            echo -e "  当前工作状态"
            echo -e "========================================${NC}"
            [ -n "$CURRENT_EPIC" ] && echo -e "  Epic: ${YELLOW}$CURRENT_EPIC${NC}"
            [ -n "$CURRENT_FEATURE" ] && echo -e "  Feature: ${YELLOW}$CURRENT_FEATURE${NC}"
            [ -n "$CURRENT_TASK" ] && echo -e "  Task: ${YELLOW}$CURRENT_TASK${NC}"
            echo -e "${GREEN}========================================${NC}"
            echo ""
        fi
    else
        log_info "无会话状态文件"
    fi
}

# 显示可用命令
show_commands() {
    echo ""
    echo -e "${BLUE}========================================"
    echo -e "  可用 Skill 命令"
    echo -e "========================================${NC}"
    echo -e "  ${GREEN}/sprint-plan${NC}      - Sprint 规划"
    echo -e "  ${GREEN}/task-breakdown${NC}  - 任务分解"
    echo -e "  ${GREEN}/architecture-review${NC} - 架构审查"
    echo -e "  ${GREEN}/code-review${NC}     - 代码审查"
    echo -e "  ${GREEN}/security-scan${NC}   - 安全扫描"
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "  可用 Agents"
    echo -e "========================================${NC}"
    echo -e "  领导层: project-manager, tech-lead"
    echo -e "  执行层: frontend-lead, backend-lead, qa-lead, devops-engineer"
    echo -e "  专家层: ui-developer, api-developer, automation-developer, test-engineer, security-expert"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 主函数
main() {
    echo ""
    echo -e "${GREEN}========================================"
    echo -e "  得物掘金工具 - 开发会话开始"
    echo -e "========================================${NC}"
    echo ""

    check_project
    check_prerequisites
    load_session_state
    show_commands

    log_success "会话初始化完成"
    exit 0
}

main "$@"
