#!/bin/bash
# pre-commit.sh: Pre-commit validation hook
# 提交前检查钩子

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 颜色
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

WARNINGS=0

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
    ((WARNINGS++))
}

log_info() {
    echo "[INFO] $*"
}

# 检查敏感数据
check_sensitive_data() {
    local file="$1"

    # 常见敏感数据模式
    local patterns=(
        "password\s*=\s*['\"][^'\"]+['\"]"
        "api_key\s*=\s*['\"][^'\"]+['\"]"
        "secret\s*=\s*['\"][^'\"]+['\"]"
        "sk-[a-zA-Z0-9]{20,}"
        "cookie.*=.*['\"][^'\"]+['\"]"
    )

    for pattern in "${patterns[@]}"; do
        if grep -qE "$pattern" "$file" 2>/dev/null; then
            log_warn "可能包含敏感数据: $file"
            log_warn "  匹配模式: $pattern"
            return 1
        fi
    done

    return 0
}

# 检查 TypeScript any 类型
check_typescript() {
    local file="$1"

    if [[ "$file" == *.ts || "$file" == *.tsx ]]; then
        # 允许的类型: : any
        # 禁止的模式: as any, <any>
        if grep -qE ":\s*any\b" "$file" 2>/dev/null; then
            log_warn "TypeScript 使用 any 类型: $file"
            grep -nE ":\s*any\b" "$file" 2>/dev/null | head -3 | while read line; do
                log_warn "  $line"
            done
        fi
    fi
}

# 检查 Python print 语句
check_python() {
    local file="$1"

    if [[ "$file" == *.py ]]; then
        if grep -qE "^\s*print\s*\(" "$file" 2>/dev/null; then
            log_warn "Python 使用 print: $file"
            log_warn "  请使用 loguru.logger"
        fi
    fi
}

# 主函数
main() {
    log_info "执行提交前检查..."

    # 获取暂存的文件
    if command -v git &> /dev/null && git rev-parse --is-inside-work-tree &> /dev/null; then
        FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || echo "")
    else
        log_info "非 Git 仓库，跳过检查"
        exit 0
    fi

    if [ -z "$FILES" ]; then
        log_info "无暂存文件"
        exit 0
    fi

    log_info "检查以下文件:"
    echo "$FILES" | while read file; do
        echo "  - $file"
    done
    echo ""

    # 检查每个文件
    echo "$FILES" | while read file; do
        full_path="$PROJECT_ROOT/$file"
        if [ -f "$full_path" ]; then
            check_sensitive_data "$full_path" || true
            check_typescript "$full_path" || true
            check_python "$full_path" || true
        fi
    done

    echo ""

    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}[WARN] 发现 $WARNINGS 个警告${NC}"
        echo -e "${YELLOW}[WARN] 请检查并确认是否继续提交${NC}"
    else
        log_info "检查通过"
    fi

    exit 0
}

main "$@"
