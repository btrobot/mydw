#Requires -Version 5.1
# Session end hook for dewugojin project

$ErrorActionPreference = 'Continue'

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path $ScriptDir "..\.."

# Paths
$SessionState = Join-Path $ProjectRoot "production\session-state\active.md"

# Colors
$OriginalForeground = $host.UI.RawUI.ForegroundColor

function Write-OK {
    param([string]$Message)
    $host.UI.RawUI.ForegroundColor = 'Green'
    Write-Host "[OK] $Message"
    $host.UI.RawUI.ForegroundColor = $OriginalForeground
}

function Write-Warn {
    param([string]$Message)
    $host.UI.RawUI.ForegroundColor = 'Yellow'
    Write-Host "[WARN] $Message"
    $host.UI.RawUI.ForegroundColor = $OriginalForeground
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
                Write-Warn "Uncommitted changes detected:"
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
        if ($content -match '## Session History|## History') {
            $newEntry = "`n`n### $timestamp`n- Session ended`n"
            $content = $content -replace '(## Session History|## History)', ("`n$newEntry`n`$1")
            Set-Content -Path $SessionState -Value $content -NoNewline
        }
    }
}

# Show next steps
function Show-NextSteps {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "  Next Steps"
    Write-Host "========================================"
    Write-Host ""
    Write-Host "  1. Ensure all changes are committed"
    Write-Host "  2. Run /code-review to review code"
    Write-Host "  3. Run /security-scan for security checks"
    Write-Host "  4. Update session-state record"
    Write-Host ""
}

# Main
function Main {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "  DewuGoJin - Session Ending"
    Write-Host "========================================"

    Test-UnsavedChanges
    Update-SessionState
    Show-NextSteps

    Write-OK "Session cleanup complete"
    exit 0
}

Main
