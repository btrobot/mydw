#Requires -Version 5.1
<#
.SYNOPSIS
    Session start hook for dewugojin project
.DESCRIPTION
    Loads session state, checks prerequisites, and shows available commands
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# Get project root (script is in .claude/hooks/)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path $ScriptDir "..\.."

# Paths
$SessionState = Join-Path $ProjectRoot "production\session-state\active.md"

# Colors (ANSI escape codes for compatibility)
$ColorReset = "`e[0m"
$ColorGreen = "`e[0;32m"
$ColorYellow = "`e[1;33m"
$ColorBlue = "`e[0;34m"
$ColorRed = "`e[0;31m"

function Write-Info {
    param([string]$Message)
    Write-Host "${ColorBlue}[INFO]${ColorReset} $Message"
}

function Write-Warn {
    param([string]$Message)
    Write-Host "${ColorYellow}[WARN]${ColorReset} $Message" -Stderr
}

function Write-Success {
    param([string]$Message)
    Write-Host "${ColorGreen}[OK]${ColorReset} $Message"
}

function Test-Command {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Get-CommandVersion {
    param([string]$Command)
    try {
        $output = & $Command --version 2>$null
        if ($output) { return $output.Trim() }
        $output = & $Command -Version 2>$null
        if ($output) { return $output.Trim() }
        return "unknown"
    }
    catch { return "unknown" }
}

# Check project structure
function Test-ProjectStructure {
    Write-Info "检查项目状态..."

    $FrontendExists = Test-Path (Join-Path $ProjectRoot "frontend")
    $BackendExists = Test-Path (Join-Path $ProjectRoot "backend")

    if ($FrontendExists -and $BackendExists) {
        Write-Success "项目结构完整"
    }
    else {
        Write-Warn "项目结构不完整 (frontend: $FrontendExists, backend: $BackendExists)"
    }
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "检查开发环境..."

    # Node.js
    if (Test-Command "node") {
        $version = Get-CommandVersion "node"
        Write-Success "Node.js: $version"
    }
    else {
        Write-Warn "Node.js 未安装"
    }

    # Python
    if (Test-Command "python") {
        $version = Get-CommandVersion "python"
        Write-Success "Python: $version"
    }
    elseif (Test-Command "python3") {
        $version = Get-CommandVersion "python3"
        Write-Success "Python: $version"
    }
    else {
        Write-Warn "Python 未安装"
    }

    # FFmpeg
    if (Test-Command "ffmpeg") {
        Write-Success "FFmpeg: 可用"
    }
    else {
        Write-Warn "FFmpeg 未安装 - AI剪辑功能不可用"
    }
}

# Load session state
function Import-SessionState {
    if (Test-Path $SessionState) {
        Write-Info "加载会话状态..."

        # Parse status block
        $content = Get-Content $SessionState -Raw

        # Extract Epic, Feature, Task
        $Epic = if ($content -match '(?s)Epic:\s*\n(.+?)(\n|$)') { $Matches[1].Trim() }
        $Feature = if ($content -match '(?s)Feature:\s*\n(.+?)(\n|$)') { $Matches[1].Trim() }
        $Task = if ($content -match '(?s)Task:\s*\n(.+?)(\n|$)') { $Matches[1].Trim() }

        if ($Task) {
            Write-Host ""
            Write-Host "${ColorGreen}========================================${ColorReset}"
            Write-Host "  当前工作状态"
            Write-Host "${ColorGreen}========================================${ColorReset}"
            if ($Epic) { Write-Host "  Epic: ${ColorYellow}$Epic${ColorReset}" }
            if ($Feature) { Write-Host "  Feature: ${ColorYellow}$Feature${ColorReset}" }
            if ($Task) { Write-Host "  Task: ${ColorYellow}$Task${ColorReset}" }
            Write-Host "${ColorGreen}========================================${ColorReset}"
            Write-Host ""
        }
    }
    else {
        Write-Info "无会话状态文件"
    }
}

# Show available commands
function Show-AvailableCommands {
    Write-Host ""
    Write-Host "${ColorBlue}========================================${ColorReset}"
    Write-Host "  可用 Skill 命令"
    Write-Host "${ColorBlue}========================================${ColorReset}"
    Write-Host "  ${ColorGreen}/sprint-plan${ColorReset}      - Sprint 规划"
    Write-Host "  ${ColorGreen}/task-breakdown${ColorReset}  - 任务分解"
    Write-Host "  ${ColorGreen}/architecture-review${ColorReset} - 架构审查"
    Write-Host "  ${ColorGreen}/code-review${ColorReset}     - 代码审查"
    Write-Host "  ${ColorGreen}/security-scan${ColorReset}   - 安全扫描"
    Write-Host ""
    Write-Host "${ColorBlue}========================================${ColorReset}"
    Write-Host "  可用 Agents"
    Write-Host "${ColorBlue}========================================${ColorReset}"
    Write-Host "  领导层: project-manager, tech-lead"
    Write-Host "  执行层: frontend-lead, backend-lead, qa-lead, devops-engineer"
    Write-Host "  专家层: ui-developer, api-developer, automation-developer, test-engineer, security-expert"
    Write-Host "${ColorBlue}========================================${ColorReset}"
    Write-Host ""
}

# Main
function Main {
    Write-Host ""
    Write-Host "${ColorGreen}========================================${ColorReset}"
    Write-Host "  得物掘金工具 - 开发会话开始"
    Write-Host "${ColorGreen}========================================${ColorReset}"
    Write-Host ""

    Test-ProjectStructure
    Test-Prerequisites
    Import-SessionState
    Show-AvailableCommands

    Write-Success "会话初始化完成"
    exit 0
}

Main
