#Requires -Version 5.1
<#
.SYNOPSIS
    Session end hook for dewugojin project
.DESCRIPTION
    Checks for unsaved changes and updates session state
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path $ScriptDir "..\.."

# Paths
$SessionState = Join-Path $ProjectRoot "production\session-state\active.md"

# Colors
$ColorReset = "`e[0m"
$ColorGreen = "`e[0;32m"
$ColorYellow = "`e[1;33m"

function Write-Success {
    param([string]$Message)
    Write-Host "${ColorGreen}[OK]${ColorReset} $Message"
}

# Check for unsaved changes
function Test-UnsavedChanges {
    Push-Location $ProjectRoot
    try {
        $IsGitRepo = $false
        try {
            $null = git rev-parse --is-inside-work-tree 2>$null
            $IsGitRepo = $LASTEXITCODE -eq 0
        }
        catch { }

        if ($IsGitRepo) {
            $null = git diff --quiet 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-Host ""
                Write-Host "${ColorYellow}[WARN] 有未提交的更改:${ColorReset}"
                git status --short
                Write-Host ""
            }
        }
    }
    finally { Pop-Location }
}

# Update session state
function Update-SessionState {
    if (Test-Path $SessionState) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $content = Get-Content $SessionState -Raw

        # Check if session history section exists
        if ($content -match '## 会话历史') {
            # Append to history
            $newEntry = @"

### $timestamp
- 会话结束
"@
            $content = $content -replace '(## 会话历史)', ("`n$newEntry`n`n`$1")
            Set-Content -Path $SessionState -Value $content -NoNewline
        }
    }
}

# Show next steps
function Show-NextSteps {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "  会话结束建议"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "  1. 确认所有更改已提交"
    Write-Host "  2. 运行 /code-review 审查代码"
    Write-Host "  3. 运行 /security-scan 检查安全"
    Write-Host "  4. 更新 session-state 记录"
    Write-Host ""
}

# Main
function Main {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "  得物掘金工具 - 会话结束"
    Write-Host "========================================"

    Test-UnsavedChanges
    Update-SessionState
    Show-NextSteps

    Write-Success "会话清理完成"
    exit 0
}

Main
