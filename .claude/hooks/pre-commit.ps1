#Requires -Version 5.1
<#
.SYNOPSIS
    Pre-commit validation hook for dewugojin project
.DESCRIPTION
    Validates staged files for sensitive data, code style issues
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path $ScriptDir "..\.."

# Colors
$ColorReset = "`e[0m"
$ColorGreen = "`e[0;32m"
$ColorYellow = "`e[1;33m"
$ColorRed = "`e[0;31m"

$Warnings = 0

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message"
}

function Write-Warn {
    param([string]$Message)
    Write-Host "${ColorYellow}[WARN]${ColorReset} $Message"
    script:WARNINGS++
}

# Check for sensitive data patterns
function Test-SensitiveData {
    param([string]$FilePath)

    # Sensitive data patterns
    $Patterns = @(
        '(?i)password\s*=\s*["''][^"'']+["'']',
        '(?i)api_key\s*=\s*["''][^"'']+["'']',
        '(?i)secret\s*=\s*["''][^"'']+["'']',
        'sk-[a-zA-Z0-9]{20,}',
        '(?i)cookie.*=.*["''][^"'']+["'']'
    )

    $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return $false }

    foreach ($pattern in $Patterns) {
        if ($content -match $pattern) {
            Write-Warn "可能包含敏感数据: $FilePath"
            Write-Warn "  匹配模式: $pattern"
            return $true
        }
    }
    return $false
}

# Check TypeScript for 'any' type usage
function Test-TypeScript {
    param([string]$FilePath)

    if ($FilePath -notmatch '\.(ts|tsx)$') { return }

    $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return }

    # Find : any patterns (but not allow comments about any)
    if ($content -match ':\s*any\b') {
        Write-Warn "TypeScript 使用 any 类型: $FilePath"
        $lines = Get-Content $FilePath
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match ':\s*any\b') {
                Write-Warn "  Line $($i + 1): $($lines[$i].Trim())"
                if ($i -ge 2) { break }  # Show max 3 lines
            }
        }
    }
}

# Check Python for print statements
function Test-Python {
    param([string]$FilePath)

    if ($FilePath -notmatch '\.py$') { return }

    $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return }

    if ($content -match '^\s*print\s*\(') {
        Write-Warn "Python 使用 print: $FilePath"
        Write-Warn "  请使用 loguru.logger"
    }
}

# Main
function Main {
    Write-Info "执行提交前检查..."

    # Check if in git repository
    $IsGitRepo = $false
    try {
        Push-Location $ProjectRoot
        $null = git rev-parse --is-inside-work-tree 2>$null
        $IsGitRepo = $LASTEXITCODE -eq 0
    }
    catch { }
    finally { Pop-Location }

    if (-not $IsGitRepo) {
        Write-Info "非 Git 仓库，跳过检查"
        exit 0
    }

    # Get staged files
    Push-Location $ProjectRoot
    try {
        $Files = git diff --cached --name-only --diff-filter=ACM 2>$null
        if ($LASTEXITCODE -ne 0) { $Files = @() }
    }
    catch { $Files = @() }
    finally { Pop-Location }

    if ($Files.Count -eq 0) {
        Write-Info "无暂存文件"
        exit 0
    }

    Write-Info "检查以下文件:"
    foreach ($file in $Files) {
        Write-Host "  - $file"
    }
    Write-Host ""

    # Check each file
    foreach ($file in $Files) {
        $FullPath = Join-Path $ProjectRoot $file
        if (Test-Path $FullPath -PathType Leaf) {
            $null = Test-SensitiveData $FullPath
            $null = Test-TypeScript $FullPath
            $null = Test-Python $FullPath
        }
    }

    Write-Host ""

    if (WARNINGS -gt 0) {
        Write-Host "${ColorYellow}[WARN] 发现 $Warnings 个警告${ColorReset}"
        Write-Host "${ColorYellow}[WARN] 请检查并确认是否继续提交${ColorReset}"
    }
    else {
        Write-Info "检查通过"
    }

    exit 0
}

Main
