# ============================================================
# SNS EMR – One-Click Integrity Check Script (Windows)
# Scope: Git, File Hash Manifest, Python Env, Alembic Schema
# Output: timestamped .log + .json summary
# ============================================================

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$root = Get-Location
$logFile = Join-Path $root "integrity-check-$timestamp.log"
$jsonFile = Join-Path $root "integrity-check-$timestamp.json"
$manifest = Join-Path $root "integrity-manifest.sha256"

# Exclusion patterns (regex, Windows paths)
$exclude = @(
  '\\.git\\',
  '\\venv\\',
  '__pycache__',
  '\\node_modules\\',
  '\\.pytest_cache\\',
  '\\.mypy_cache\\',
  '\\.ruff_cache\\'
)

# Exclude generated artifacts by name
$excludeNames = @(
  'integrity-manifest.sha256',
  "installed-freeze.txt",
  "installed-freeze-$timestamp.txt"
)

function IsExcludedPath {
    param([string]$fullName)
    foreach ($pat in $exclude) {
        if ($fullName -match $pat) { return $true }
    }
    return $false
}

function IsExcludedName {
    param([string]$name)
    foreach ($n in $excludeNames) {
        if ($name -ieq $n) { return $true }
    }
    # exclude all prior logs/freeze snapshots too
    if ($name -match '^integrity-check-.*\.(log|json)$') { return $true }
    if ($name -match '^installed-freeze-.*\.txt$') { return $true }
    return $false
}

function Log {
    param ($message)
    $line = "$(Get-Date -Format "yyyy-MM-dd HH:mm:ss")  $message"
    Write-Host $line
    Add-Content -Path $logFile -Value $line -Encoding utf8
}

# Result object for JSON
$result = [ordered]@{
  timestamp = (Get-Date).ToString("o")
  root = "$root"
  git = [ordered]@{
    commit = $null
    modified_tracked = @()
    untracked = @()
    fsck_output = @()
  }
  files = [ordered]@{
    manifest_path = "$manifest"
    manifest_created = $false
    changed = @()
    missing = @()
    verified = $false
  }
  python = [ordered]@{
    pip_check = @()
    freeze_file = $null
  }
  alembic = [ordered]@{
    current = @()
    heads = @()
    matches = $false
  }
}

Log "=== SNS EMR Integrity Check START ==="
Log "Root directory: $root"

# ------------------------------------------------------------
# 1) Git Integrity
# ------------------------------------------------------------
Log "--- Git status check ---"
$gs = git status --porcelain
if ($gs) {
    foreach ($line in $gs) {
        if ($line -match '^\?\? ') {
            $path = $line.Substring(3).Trim()
            $result.git.untracked += $path
            Log "UNTRACKED: $path"
        } else {
            $result.git.modified_tracked += $line.Trim()
            Log "MODIFIED: $line"
        }
    }
} else {
    Log "Git working tree: CLEAN"
}

Log "--- Git fsck (repository integrity) ---"
$fs = git fsck --full 2>&1
foreach ($line in $fs) { $result.git.fsck_output += $line; Log $line }
if (-not $fs) { Log "git fsck: no output (OK)" }

Log "--- Git commit hash ---"
$commit = git rev-parse HEAD
$result.git.commit = "$commit"
Log "DEPLOYED COMMIT: $commit"

# ------------------------------------------------------------
# 2) File Integrity (SHA-256)
# ------------------------------------------------------------
# Build file list (excluding manifest/logs/venv/etc.)
Log "--- Building file list for hashing ---"
$files = Get-ChildItem -Recurse -File |
  Where-Object {
    -not (IsExcludedPath $_.FullName) -and -not (IsExcludedName $_.Name)
  } |
  Sort-Object FullName

if (-Not (Test-Path $manifest)) {
    Log "Manifest not found. Creating baseline manifest."
    $hashLines = foreach ($f in $files) {
        $h = (Get-FileHash $f.FullName -Algorithm SHA256).Hash
        "$h  $($f.FullName)"
    }
    $hashLines | Out-File $manifest -Encoding ascii
    $result.files.manifest_created = $true
    Log "Baseline integrity-manifest.sha256 created."
}
else {
    Log "--- Verifying file integrity against manifest ---"
    $result.files.verified = $true

    Get-Content $manifest | ForEach-Object {
        if (-not $_) { return }
        $parts = $_ -split '  ', 2
        if ($parts.Count -lt 2) { return }

        $expectedHash = $parts[0].Trim()
        $path = $parts[1].Trim()

        # Skip verifying excluded artifacts even if present in old manifest
        $name = Split-Path $path -Leaf
        if (IsExcludedName $name) { return }
        if (IsExcludedPath $path) { return }

        if (Test-Path $path) {
            $actualHash = (Get-FileHash $path -Algorithm SHA256).Hash
            if ($actualHash -ne $expectedHash) {
                $result.files.changed += $path
                Log "CHANGED FILE: $path"
            }
        }
        else {
            $result.files.missing += $path
            Log "MISSING FILE: $path"
        }
    }
}

# ------------------------------------------------------------
# 3) Python Environment Integrity
# ------------------------------------------------------------
Log "--- Python dependency check (pip check) ---"
$pip = pip check 2>&1
foreach ($line in $pip) { $result.python.pip_check += $line; Log $line }
if (-not $pip) { Log "pip check: no output (OK)" }

Log "--- Freezing Python environment ---"
$pipFreeze = Join-Path $root "installed-freeze-$timestamp.txt"
pip freeze | Out-File $pipFreeze -Encoding ascii
$result.python.freeze_file = "$pipFreeze"
Log "Python package snapshot saved: $pipFreeze"

# ------------------------------------------------------------
# 4) Alembic Schema Integrity
# ------------------------------------------------------------
Log "--- Alembic current ---"
$ac = alembic current 2>&1
foreach ($line in $ac) { $result.alembic.current += $line; Log $line }

Log "--- Alembic heads ---"
$ah = alembic heads 2>&1
foreach ($line in $ah) { $result.alembic.heads += $line; Log $line }

# Basic match check (string containment)
$currLine = ($ac | Where-Object { $_ -match '^\w+' } | Select-Object -Last 1)
$headLine = ($ah | Where-Object { $_ -match '^\w+' } | Select-Object -Last 1)
if ($currLine -and $headLine -and ($currLine.Split()[0] -eq $headLine.Split()[0])) {
    $result.alembic.matches = $true
    Log "Alembic: current matches heads (OK)"
} else {
    Log "Alembic: current does NOT match heads (RISK)"
}

# ------------------------------------------------------------
# Save JSON summary
# ------------------------------------------------------------
($result | ConvertTo-Json -Depth 6) | Out-File $jsonFile -Encoding utf8
Log "JSON summary saved: $jsonFile"

Log "=== SNS EMR Integrity Check COMPLETE ==="
Log "Log file: $logFile"

Write-Host ""
Write-Host "Integrity check complete." -ForegroundColor Green
Write-Host "Log:  $logFile"
Write-Host "JSON: $jsonFile"
