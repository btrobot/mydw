---
name: security-scan
description: "安全扫描 - 检查代码漏洞和安全问题"
argument-hint: "[范围: full|quick|dependencies] [路径: backend/|frontend/]"
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Security Scan Skill

安全扫描工作流，检查代码中的安全漏洞。

## 触发方式

```
/security-scan
/security-scan quick
/security-scan full
/security-scan dependencies
/security-scan backend/
/security-scan frontend/
```

## Context Detection

**IMPORTANT**: Before starting the scan, determine scope from the argument:

1. If the argument is a **mode** (`quick`/`full`/`dependencies`): scan all code using that mode
2. If the argument is a **path**:
   - Path starts with `backend/` or is a `.py` file → **Backend scope**: only scan Python files, skip npm audit, focus on SQLi/credential/logging patterns
   - Path starts with `frontend/` or is a `.ts`/`.tsx` file → **Frontend scope**: only scan TypeScript files, skip pip-audit, focus on XSS/console.log/sensitive storage patterns
3. If **no argument**: default to `quick` mode, scan all code
4. If argument combines mode + path (e.g., `full backend/`): apply both filters

## 扫描范围

### 快速扫描 (quick)

检查最常见的安全问题。

```bash
# 硬编码密钥
grep -rn "password\s*=\s*['\"]" --include="*.py" backend/
grep -rn "api_key\s*=\s*['\"]" --include="*.py" backend/
grep -rn "sk-[a-zA-Z0-9]" backend/

# 日志泄露
grep -rn "cookie" --include="*.py" backend/ | grep "logger"
grep -rn "password" --include="*.py" backend/ | grep "logger"

# SQL 注入
grep -rn "execute.*f\"" backend/
grep -rn "text.*%" backend/
```

### 完整扫描 (full)

全面检查所有安全问题。

| 检查项 | 说明 |
|--------|------|
| 硬编码密钥 | API Key、密码、Token |
| SQL 注入 | 未参数化的 SQL |
| XSS | 未转义的用户输入 |
| 敏感数据暴露 | 日志、响应中的敏感数据 |
| 不安全依赖 | 有漏洞的第三方库 |
| 配置错误 | 不安全的默认配置 |

### 依赖扫描 (dependencies)

检查第三方库漏洞。

```bash
# Python
pip-audit
safety check

# Node.js
npm audit
```

## 执行步骤

### Step 1: 收集代码

读取所有源代码文件。

### Step 2: 模式扫描

```python
# 高风险模式
patterns = [
    # 硬编码密码
    (r"password\s*=\s*['\"][^'\"]+['\"]", "硬编码密码"),
    (r"api_key\s*=\s*['\"][^'\"]+['\"]", "硬编码 API Key"),

    # SQL 注入
    (r"execute\s*\(['\"].*%", "SQL 注入风险"),
    (r"text\s*\(['\"].*%s.*['\"]", "SQL 注入风险"),

    # 日志泄露
    (r"logger\.(info|debug).*cookie", "Cookie 日志泄露"),
    (r"logger\.(info|debug).*password", "密码日志泄露"),

    # 危险函数
    (r"eval\s*\(", "危险函数 eval"),
    (r"exec\s*\(", "危险函数 exec"),
]
```

### Step 3: 生成报告

```markdown
## 安全扫描报告

**扫描范围**: full
**日期**: YYYY-MM-DD
**扫描文件**: 45

---

### 发现问题

| 严重性 | 文件 | 行号 | 问题 | 建议 |
|--------|------|------|------|------|
| 🔴 CRITICAL | api/auth.py | 42 | 硬编码密码 | 使用环境变量 |
| 🟠 HIGH | services/user.py | 78 | SQL 注入风险 | 使用参数化查询 |
| 🟡 MEDIUM | utils/logger.py | 23 | Cookie 日志泄露 | 脱敏处理 |
| 🟢 LOW | frontend/api.ts | 56 | console.log 调试代码 | 生产环境移除 |

---

### 风险摘要

- 🔴 CRITICAL: 1
- 🟠 HIGH: 1
- 🟡 MEDIUM: 1
- 🟢 LOW: 1

---

### 详细问题

#### 🔴 CRITICAL: 硬编码密码

**文件**: backend/core/config.py
**行号**: 5

**代码**:
```python
SECRET_KEY = "sk-1234567890abcdef"
```

**风险**: 代码泄露导致密钥暴露

**修复**:
```python
import os

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY 环境变量未设置")
```

---

### 建议

1. **立即修复**: CRITICAL 和 HIGH 问题
2. **本周修复**: MEDIUM 问题
3. **后续处理**: LOW 问题

---

### 安全最佳实践

#### Python
- ✅ 使用 `os.environ.get()` 获取密钥
- ✅ 使用 Pydantic 验证输入
- ✅ 使用 SQLAlchemy ORM
- ✅ 使用 loguru 记录日志

#### TypeScript
- ✅ 使用 `.env` 文件管理配置
- ✅ 不在前端存储敏感信息
- ✅ 使用 TypeScript 类型
- ❌ 避免 console.log
```

## 输出

更新安全跟踪：

```markdown
## 安全跟踪

| ID | 问题 | 严重性 | 状态 | 修复日期 |
|----|------|--------|------|----------|
| SEC-001 | 硬编码密码 | 🔴 | 待修复 | - |
| SEC-002 | SQL 注入 | 🟠 | 待修复 | - |
| SEC-003 | Cookie 日志 | 🟡 | 待修复 | - |
```

## 升级

如果发现 CRITICAL 或 HIGH 问题，立即升级：

```markdown
## 安全升级

### 🔴 CRITICAL: 硬编码密码

**问题**: backend/core/config.py 包含硬编码密码

**风险**: 代码泄露导致账号被劫持

**建议**: 立即修复

**请求**: User (Product Owner) 批准紧急修复
```

同时更新 `production/session-state/active.md` 安全扫描结果。
