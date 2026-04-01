#Requires -Version 5.1
# Session start hook for dewugojin project

$ErrorActionPreference = 'Stop'

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Join-Path $ScriptDir "..\.."
$SessionState = Join-Path $ProjectRoot "production\session-state\active.md"

# Colors using Write-Host with foreground color
$OriginalForeground = $host.UI.RawUI.ForegroundColor

function Write-Info {
    $host.UI.RawUI.ForegroundColor = 'Cyan'
    Write-Host "[INFO] $($args -join ' ')"
    $host.UI.RawUI.ForegroundColor = $OriginalForeground
}

function Write-OK {
    $host.UI.RawUI.ForegroundColor = 'Green'
    Write-Host "[OK] $($args -join ' ')"
    $host.UI.RawUI.ForegroundColor = $OriginalForeground
}

function Write-Warn {
    $host.UI.RawUI.ForegroundColor = 'Yellow'
    Write-Host "[WARN] $($args -join ' ')"
    $host.UI.RawUI.ForegroundColor = $OriginalForeground
}

function Write-Header {
    $host.UI.RawUI.ForegroundColor = 'Green'
    Write-Host "========================================"
    Write-Host "  $($args -join ' ')"
    Write-Host "========================================"
    $host.UI.RawUI.ForegroundColor = $OriginalForeground
}

function Write-Status {
    param($Label, $Value)
    if ($Value -and $Value.Trim().Length -gt 0) {
        Write-Host "  $Label " -NoNewline
        $host.UI.RawUI.ForegroundColor = 'Yellow'
        Write-Host $Value.Trim()
        $host.UI.RawUI.ForegroundColor = $OriginalForeground
    }
}

Write-Host ""
Write-Header "DewuGoJin - Session Started"

Write-Info "Checking project structure..."

# Check frontend
$FrontendPath = Join-Path $ProjectRoot "frontend"
if (Test-Path $FrontendPath) {
    Write-OK "Frontend: Found"
} else {
    Write-Warn "Frontend: Not found"
}

# Check backend
$BackendPath = Join-Path $ProjectRoot "backend"
if (Test-Path $BackendPath) {
    Write-OK "Backend: Found"
} else {
    Write-Warn "Backend: Not found"
}

Write-Host ""
Write-Info "Checking prerequisites..."

# Node.js
if ($null -ne (Get-Command node -ErrorAction SilentlyContinue)) {
    $version = & node --version 2>$null
    Write-OK "Node.js: $version"
} else {
    Write-Warn "Node.js: Not installed"
}

# Python
if ($null -ne (Get-Command python -ErrorAction SilentlyContinue)) {
    $version = & python --version 2>$null
    Write-OK "Python: $version"
} elseif ($null -ne (Get-Command python3 -ErrorAction SilentlyContinue)) {
    $version = & python3 --version 2>$null
    Write-OK "Python: $version"
} else {
    Write-Warn "Python: Not installed"
}

# FFmpeg
if ($null -ne (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-OK "FFmpeg: Available"
} else {
    Write-Warn "FFmpeg: Not installed (AI editing unavailable)"
}

# Load session state
Write-Host ""
if (Test-Path $SessionState) {
    Write-Info "Loading session state..."

    $content = Get-Content $SessionState -Raw

    # Parse the status block between <!-- STATUS --> and <!-- /STATUS -->
    if ($content -match '(?s)<!-- STATUS -->.*?<!-- /STATUS -->') {
        $statusBlock = $Matches[0]

        # Extract values - value is on same line as label (e.g., "Epic: value")
        # Must have a literal space after colon, then value until end of line
        # Handle both CRLF (Windows) and LF (Unix) line endings
        $Epic = if ($statusBlock -match '(?s)Epic: (.+?)\r?\n') { $Matches[1].Trim() } else { $null }
        $Feature = if ($statusBlock -match '(?s)Feature: (.+?)\r?\n') { $Matches[1].Trim() } else { $null }
        $Task = if ($statusBlock -match '(?s)Task: (.+?)\r?\n') { $Matches[1].Trim() } else { $null }

        # Only show status if we have actual content
        if ($Task -and $Task.Length -gt 0) {
            Write-Host ""
            Write-Header "Current Status"
            if ($Epic) { Write-Status "Epic:" $Epic }
            if ($Feature) { Write-Status "Feature:" $Feature }
            if ($Task) { Write-Status "Task:" $Task }
        }
    }
} else {
    Write-Info "No session state file"
}

# Show available commands
Write-Host ""
Write-Header "Available Skills"
Write-Host "  /sprint-plan        - Sprint planning"
Write-Host "  /task-breakdown    - Task breakdown"
Write-Host "  /architecture-review - Architecture review"
Write-Host "  /code-review       - Code review"
Write-Host "  /security-scan     - Security scan"
Write-Host ""

Write-OK "Session initialized"
exit 0
