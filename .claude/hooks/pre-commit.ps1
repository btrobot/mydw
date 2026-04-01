#Requires -Version 5.1
# Pre-commit validation hook for dewugojin project

$ErrorActionPreference = 'Continue'

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path $ScriptDir "..\.."

# Variables
$WarningCount = 0

# Colors
$OriginalForeground = $host.UI.RawUI.ForegroundColor

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message"
}

function Write-Warn {
    param([string]$Message)
    $host.UI.RawUI.ForegroundColor = 'Yellow'
    Write-Host "[WARN] $Message"
    $host.UI.RawUI.ForegroundColor = $OriginalForeground
    $script:WarningCount++
}

# Check for sensitive data patterns
function Test-SensitiveData {
    param([string]$FilePath)

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
            Write-Warn "May contain sensitive data: $FilePath"
            Write-Warn "  Pattern: $pattern"
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

    if ($content -match ':\s*any\b') {
        Write-Warn "TypeScript uses 'any' type: $FilePath"
        $lines = Get-Content $FilePath
        $foundCount = 0
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match ':\s*any\b') {
                Write-Warn "  Line $($i + 1): $($lines[$i].Trim())"
                $foundCount++
                if ($foundCount -ge 3) { break }
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
        Write-Warn "Python uses print: $FilePath"
        Write-Warn "  Please use loguru.logger instead"
    }
}

# Main
function Main {
    Write-Info "Running pre-commit checks..."

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
        Write-Info "Not a git repository, skipping checks"
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
        Write-Info "No staged files"
        exit 0
    }

    Write-Info "Checking files:"
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

    if ($WarningCount -gt 0) {
        $host.UI.RawUI.ForegroundColor = 'Yellow'
        Write-Host "[WARN] Found $WarningCount warning(s)"
        $host.UI.RawUI.ForegroundColor = $OriginalForeground
        Write-Host "[WARN] Please review and confirm before committing"
    }
    else {
        Write-Info "All checks passed"
    }

    exit 0
}

Main
